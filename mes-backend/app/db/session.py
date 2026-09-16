"""Engine + session. Đồng bộ, không async — xem BE-PLAN §1."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.common.config import settings

engine = create_engine(
    settings.database.url,
    pool_size=settings.database.pool_size,
    max_overflow=settings.database.max_overflow,
    pool_pre_ping=True,           # kết nối chết qua đêm thì tự thay
    echo=settings.database.echo,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


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
