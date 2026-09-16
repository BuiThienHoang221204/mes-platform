"""Màn hình Kế hoạch — vòng đời một lệnh trước khi xuống xưởng. Vai PLANNER.

    GET  /mos                          danh sách lệnh, lọc theo trạng thái
    POST /mos                          tạo một lệnh
    POST /mos/import                   nhập nhiều lệnh từ một file CSV
    POST /mos/{code}/submit            chốt lệnh + mở vòng 1 → vào hàng chờ Kho
    POST /mos/{code}/cancel            huỷ kèm lý do
    GET  /mos/{code}                   xem một lệnh

Ranh giới của module này là mốc Submit: trước đó lệnh còn sửa, sau đó mã / SL /
thời gian khoá cứng — nhập sai thì HUỶ rồi tạo lệnh mới, không sửa, không xoá (§4A).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep
from app.common.schemas import OkOut
from app.common.security.permissions import PLANNER, VIEW
from app.common.vocab.enums import MoStatus
from app.modules.mo import repository as mo_repo
from app.modules.mo import service as mo_service
from app.modules.mo.schemas import MoCancelIn, MoCreateIn, MoImportIn, MoOut

router = APIRouter(tags=["mo"])


@router.post("/mos", response_model=list[MoOut])
def create_mo(body: MoCreateIn, db: DbDep, actor: ActorDep) -> list:
    """Tạo MỘT lệnh, trạng thái DRAFT — chưa xuống xưởng."""
    actor.require_role(PLANNER)
    item = mo_service.NewMo(body.code, body.product_name, body.quantity,
                            body.required_production_min * 60, body.pcs_per_box)
    made = mo_service.create(db, [item], uuid.UUID(actor.user_id))
    return [_mo_out(m) for m in made]


@router.post("/mos/import", response_model=list[MoOut])
def import_csv(body: MoImportIn, db: DbDep, actor: ActorDep) -> list:
    """Nhập nhiều lệnh từ CSV 4 cột: Mã · Tên hàng · Số lượng · TG yêu cầu (phút).
    Mã lấy nguyên từ file — hệ thống KHÔNG tự sinh mã (#36)."""
    actor.require_role(PLANNER)
    items = mo_service.parse_csv(body.csv)
    made = mo_service.create(db, items, uuid.UUID(actor.user_id))
    return [_mo_out(m) for m in made]


@router.post("/mos/{code}/submit", response_model=OkOut)
def submit_mo(code: str, db: DbDep, actor: ActorDep) -> OkOut:
    """Chốt lệnh và MỞ VÒNG 1 — từ đây MO có mặt ở hàng chờ Kho.
    Sau bước này mã / SL / thời gian khoá cứng (§4A)."""
    actor.require_role(PLANNER)
    mo_service.submit(db, code, uuid.UUID(actor.user_id))
    return OkOut(message=f"{code} đã Submit — khoá cứng mã/SL/thời gian (§4A)")


@router.post("/mos/{code}/cancel", response_model=OkOut)
def cancel_mo(code: str, body: MoCancelIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Huỷ lệnh kèm lý do. Bản ghi vẫn giữ — muốn sửa thì tạo lệnh mới."""
    actor.require_role(PLANNER)
    mo_service.cancel(db, code, body.reason, uuid.UUID(actor.user_id))
    return OkOut(message=f"{code} đã huỷ. Bản ghi vẫn giữ — tạo lệnh mới để thay (§4A)")


@router.get("/mos", response_model=list[MoOut])
def list_mos(db: DbDep, actor: ActorDep, status: MoStatus | None = None) -> list:
    """Danh sách lệnh, mới nhất trước. `status` để lọc — màn Kế hoạch lọc DRAFT.

    Quyền y hệt `GET /mos/{code}`: chỉ-đọc và mọi phòng ban đều xem được trạm 4
    (§9b). Mở chi tiết mà khoá danh sách thì mới là chỗ khó hiểu.
    """
    actor.require_step(4, VIEW)
    return [_mo_out(m) for m in mo_repo.list_mos(db, status=status)]


@router.get("/mos/{code}", response_model=MoOut)
def get_mo(code: str, db: DbDep, actor: ActorDep) -> MoOut:
    """Xem một lệnh: tên hàng, SL, đơn vị, trạng thái, TG yêu cầu."""
    # Trước đây KHÔNG kiểm gì — ai đăng nhập cũng đọc được. Mọi phòng ban đều
    # xem được trạm 4 (§9b.4) nên câu này hiện đúng với tất cả, và sẽ bắt đầu
    # chặn khi có vai không được xem trạm 4 (ví dụ vai cho khách xem tiến độ).
    actor.require_step(4, VIEW)
    return _mo_out(mo_repo.get_mo(db, code))


def _mo_out(mo) -> MoOut:
    return MoOut(code=mo.code, product_name=mo.product_name, quantity=mo.quantity,
                   unit=mo.unit, pcs_per_box=mo.pcs_per_box, status=mo.status,
                   required_production_sec=mo.required_production_sec)
