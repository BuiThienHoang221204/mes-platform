"""Điểm vào. Gắn router, middleware, và MỘT chỗ duy nhất đổi lỗi thành HTTP."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError, InterfaceError, OperationalError, SQLAlchemyError

from app.common import read_cache
from app.common.config import settings
from app.common.deps import ActorDep
from app.common.errors import DomainError, translate_db_error
from app.common.logging import new_request_id, request_id_var, setup_logging
from app.common.security.permissions import PLANNER
from app.common.single_process import assert_single_process
from app.common.vocab.error_codes import Err
from app.db.session import db_target, log_db_status, probe_db
from app.router import router

setup_logging()
log = logging.getLogger("mes")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    assert_single_process()
    log_db_status()
    yield

app = FastAPI(
    title="MES Platform API",
    version="0.1.0",
    description="""Sáu trạm quét · vòng chạy · KPI thời gian. Xem BRD-v2-chot.md.

**Đăng nhập ngay trên trang này:** gọi `POST /v1/auth/login` với
`{"emp_code": "NV001", "pin": "1234"}` — trình duyệt nhận cookie httpOnly và tự
gửi kèm mọi lời gọi sau, **không cần bấm Authorize**.

Nút **Authorize** dành cho hai trường hợp khác:

* `bearer` — dán access token khi gọi bằng curl hoặc từ máy quét
* `station` — dán token thiết bị (`X-Station-Token`) để thử `/v1/scan`
""",
    # Giữ token đã Authorize qua mỗi lần tải lại trang.
    swagger_ui_parameters={"persistAuthorization": True},
    lifespan=lifespan,
)
# Cookie chỉ đi kèm request khi CORS cho phép mang thông tin đăng nhập. Vì vậy
# KHÔNG được dùng allow_origins=["*"] — trình duyệt từ chối cặp đó, và cookie sẽ
# im lặng không được gửi. Phải liệt kê đúng origin của FE (MES_CORS_ORIGINS).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id_var.set(new_request_id())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id_var.get()
    return response


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status,
                        content={"code": exc.code, "message": exc.message})


CONNECT_ERRORS = (OperationalError, InterfaceError)


def _is_connect_error(exc: SQLAlchemyError) -> bool:
    if not isinstance(exc, CONNECT_ERRORS):
        return False
    if getattr(exc, "connection_invalidated", False):
        return True
    return getattr(getattr(exc, "orig", None), "sqlstate", None) is None


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Luật nằm ở DB nên lỗi DB là lỗi NGHIỆP VỤ — dịch, đừng trả 500.

    Một bảng ánh xạ duy nhất trong core/errors.py; router và service không bắt lỗi này.
    """
    if _is_connect_error(exc):
        log.error(
            "KHÔNG KẾT NỐI ĐƯỢC CSDL khi xử lý %s %s — %s | %s",
            request.method,
            request.url.path,
            db_target(),
            getattr(exc, "orig", exc),
        )
        return JSONResponse(
            status_code=503,
            content={"code": Err.DB_UNAVAILABLE,
                     "message": "Máy chủ chưa kết nối được cơ sở dữ liệu"},
        )

    translated = translate_db_error(exc)
    if translated is not None:
        return JSONResponse(status_code=translated.status,
                            content={"code": translated.code, "message": translated.message})
    log.exception("Lỗi CSDL không nhận ra")
    if isinstance(exc, DBAPIError) and settings.env != "prod":
        return JSONResponse(status_code=500, content={"code": Err.DB, "message": str(exc.orig)})
    return JSONResponse(status_code=500,
                        content={"code": Err.DB, "message": "Lỗi cơ sở dữ liệu"})


@app.get("/healthz", tags=["ops"])
def healthz() -> dict:
    return {"ok": True}


@app.get("/ops/cache-stats", tags=["ops"])
def cache_stats(actor: ActorDep) -> dict:
    """Cache đọc có đỡ được gì không — `hits`, `misses`, `waits`.

    Chỉ số đếm, không có dữ liệu nghiệp vụ. Cách đọc: `docs/RA-SOAT-POLLING.md`.

    Dành cho điều độ: đây là số liệu vận hành cả xưởng, không gắn trạm nào.
    """
    actor.require_role(PLANNER)
    return read_cache.stats()


@app.get("/readyz", tags=["ops"])
def readyz() -> JSONResponse:
    reason = probe_db()
    if reason is None:
        return JSONResponse(content={"ok": True, "db": True, "target": db_target()})
    log.error("KHÔNG KẾT NỐI ĐƯỢC CSDL — %s | %s", db_target(), reason)
    return JSONResponse(
        status_code=503,
        content={"ok": False, "db": False, "target": db_target(),
                 "code": Err.DB_UNAVAILABLE, "reason": reason},
    )
