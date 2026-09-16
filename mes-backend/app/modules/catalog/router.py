"""Danh mục cho các ô chọn của FE, kèm phần quản trị chuyền.

    GET    /lines                      14 chuyền, cả chuyền đã tắt
    POST   /lines                      thêm chuyền — vai PLANNER
    DELETE /lines/{code}               xoá chuyền chưa ai dùng — vai PLANNER
    GET    /reasons                    mã lý do, lọc theo `group`

Hai endpoint ĐỌC gọi thẳng repository: không có luật nghiệp vụ nào để service lo.
Hai endpoint GHI thì qua `service.py`, vì chúng cần một ranh giới giao dịch.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.common.deps import ActorDep, DbDep
from app.common.schemas import OkOut
from app.common.security.permissions import PLANNER
from app.modules.catalog import repository as catalog_repo
from app.modules.catalog import service as catalog_service
from app.modules.catalog.schemas import CatalogLine, CatalogReason, LineCreateIn

router = APIRouter(tags=["catalog"])


@router.get("/lines", response_model=list[CatalogLine])
def list_lines(db: DbDep, actor: ActorDep) -> list:
    """Danh sách 14 chuyền, cho ô chọn của FE."""
    return catalog_repo.list_lines(db)


@router.post("/lines", response_model=CatalogLine, status_code=status.HTTP_201_CREATED)
def create_line(body: LineCreateIn, db: DbDep, actor: ActorDep) -> CatalogLine:
    """Thêm một chuyền. Số `id` do máy chủ cấp, FE chỉ gửi mã và tên."""
    actor.require_role(PLANNER)
    line = catalog_service.create_line(db, code=body.code, name=body.name)
    return CatalogLine.model_validate(line, from_attributes=True)


@router.delete("/lines/{code}", response_model=OkOut)
def delete_line(code: str, db: DbDep, actor: ActorDep) -> OkOut:
    """Xoá hẳn một chuyền — CHỈ được khi chuyền chưa từng chạy MO nào.

    Chuyền đã có lịch sử thì trả 409: xoá đi là mọi đoạn chuyền cũ mất chỗ trỏ về.
    Muốn cho chuyền nghỉ thì TẮT nó (`is_active`), đừng xoá.
    """
    actor.require_role(PLANNER)
    catalog_service.delete_line(db, code)
    return OkOut(message=f"Đã xoá chuyền {code.strip().upper()}")


@router.get("/reasons", response_model=list[CatalogReason])
def list_reasons(db: DbDep, actor: ActorDep, group: str | None = None) -> list:
    """Danh mục mã lý do. `group` để lọc đúng nhóm của ô đang mở."""
    return catalog_repo.list_reasons(db, group)
