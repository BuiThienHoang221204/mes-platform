"""Gộp router của 10 tính năng có endpoint. Tiền tố `/v1` đặt DUY NHẤT ở đây.

THỨ TỰ include_router là HÀNH VI: Starlette dò route theo thứ tự đăng ký, mà
`GET /mos/{code}` ở `mo/` còn `GET /mos/{code}/trace` ở `board/`.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.modules.auth import router as auth_router
from app.modules.board import router as board_router
from app.modules.catalog import router as catalog_router
from app.modules.mo import router as mo_router
from app.modules.packing import router as packing_router
from app.modules.production import router as production_router
from app.modules.qc import router as qc_router
from app.modules.scan import router as scan_router
from app.modules.warehouse_in import router as warehouse_in_router
from app.modules.warehouse_out import router as warehouse_router

router = APIRouter(prefix="/v1")

for _sub in (
    auth_router.router,
    mo_router.router,
    scan_router.router,
    warehouse_router.router,
    qc_router.router,
    production_router.router,
    packing_router.router,
    warehouse_in_router.router,
    board_router.router,
    catalog_router.router,
):
    router.include_router(_sub)

__all__ = ["router"]
