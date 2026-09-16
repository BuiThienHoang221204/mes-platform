"""Luật của danh mục chuyền — phần GHI. Vai PLANNER, router canh.

    create_line(db, code, name)            thêm chuyền, chuẩn hoá mã
    delete_line(db, code)                  xoá chuyền chưa ai dùng

Phần ĐỌC không có ở đây: router gọi thẳng repository vì không có luật nào để lo.
Phần ghi thì buộc phải có tầng này — `get_db` KHÔNG commit hộ, nên thiếu
`@transactional` là câu INSERT biến mất lặng lẽ.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.uow import transactional
from app.modules.catalog import repository as catalog_repo
from app.modules.catalog.models import Line


@transactional
def create_line(db: Session, *, code: str, name: str | None = None) -> Line:
    """Thêm một chuyền. Mã chuẩn hoá về CHỮ HOA trước khi ghi.

    Không chuẩn hoá thì `l15` và `L15` lọt qua ràng buộc UNIQUE thành hai chuyền.
    """
    return catalog_repo.create_line(db, code=code.strip().upper(), name=name)


@transactional
def delete_line(db: Session, code: str) -> None:
    """Xoá một chuyền. Chuyền đã chạy MO thì khoá ngoại `line_segment` chặn."""
    catalog_repo.delete_line(db, code.strip().upper())
