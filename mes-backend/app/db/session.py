"""Engine + session. Đồng bộ, không async — xem BE-PLAN §1."""

from __future__ import annotations

import logging
from collections.abc import Iterator

from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session, sessionmaker

from app.common.config import settings

log = logging.getLogger("mes.db")

engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=True,
    echo=settings.database.echo,
    future=True,
    connect_args={"connect_timeout": settings.database.connect_timeout},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def db_target() -> str:
    url = make_url(settings.database.url)
    return f"{url.host}:{url.port or 5432}/{url.database} (user={url.username})"


def probe_db() -> str | None:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def log_db_status() -> bool:
    reason = probe_db()
    if reason is None:
        log.info("Kết nối CSDL OK — %s", db_target())
        return True
    log.error(
        "KHÔNG KẾT NỐI ĐƯỢC CSDL — %s | %s | Postgres chưa chạy, "
        "sai mật khẩu, hoặc cổng đang bị tiến trình khác chiếm",
        db_target(),
        reason,
    )
    return False


def get_db() -> Iterator[Session]:
    """Dependency của FastAPI: cấp session, KHÔNG quản giao dịch.

    Ranh giới giao dịch nằm ở service, đánh dấu bằng `@transactional`
    (`app/common/uow.py`). Lý do không đặt ở đây: khoá dòng `SELECT … FOR UPDATE`
    chỉ sống trong một giao dịch, mà chỉ service mới biết khoá cái gì và giữ tới
    đâu. Đặt ở đây thì mọi request — kể cả GET — đều ôm một giao dịch.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
