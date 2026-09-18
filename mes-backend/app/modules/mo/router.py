"""Màn hình Kế hoạch — vòng đời một lệnh trước khi xuống xưởng. Vai PLANNER.

    GET  /mos                          MỘT TRANG sổ lệnh — lọc trạng thái và ngày tạo
    POST /mos                          tạo một lệnh
    POST /mos/import-excel                     nhập nhiều lệnh từ tệp Excel đã tách cột
    POST /mos/{code}/submit            chốt lệnh + mở vòng 1 → vào hàng chờ Kho
    POST /mos/{code}/cancel            huỷ kèm lý do
    GET  /mos/{code}                   xem một lệnh

Ranh giới của module này là mốc Submit: trước đó lệnh còn sửa, sau đó mã / SL /
thời gian khoá cứng — nhập sai thì HUỶ rồi tạo lệnh mới, không sửa, không xoá (§4A).
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter

from app.common.deps import ActorDep, DbDep, PageDep
from app.common.errors import Invalid
from app.common.schemas import OkOut, Page
from app.common.security.permissions import PLANNER, VIEW
from app.common.vocab.enums import MoStatus
from app.modules.mo import repository as mo_repo
from app.modules.mo import service as mo_service
from app.modules.mo.schemas import (
    MoBatchIn,
    MoCancelBatchIn,
    MoCancelIn,
    MoCreateIn,
    MoExcelImportIn,
    MoOut,
)

router = APIRouter(tags=["mo"])


@router.post("/mos", response_model=list[MoOut])
def create_mo(body: MoCreateIn, db: DbDep, actor: ActorDep) -> list:
    """Tạo MỘT lệnh, trạng thái DRAFT — chưa xuống xưởng."""
    actor.require_role(PLANNER)
    item = mo_service.NewMo(body.code, body.product_name, body.quantity,
                            body.required_production_min * 60, body.pcs_per_box)
    made = mo_service.create(db, [item], uuid.UUID(actor.user_id))
    return [_mo_out(m) for m in made]


@router.post("/mos/import-excel", response_model=list[MoOut])
def import_excel(body: MoExcelImportIn, db: DbDep, actor: ActorDep) -> list:
    """Nhập nhiều lệnh từ tệp Excel đã tách cột sẵn ở trình duyệt.

    Nhận danh sách có cấu trúc chứ không nhận văn bản CSV: tên con hàng có
    dấu phẩy sẽ làm lệch cột và sinh ra lệnh sai mà không báo gì. Mã lấy nguyên
    từ tệp — hệ thống KHÔNG tự sinh mã (#36).
    """
    actor.require_role(PLANNER)
    items = [
        mo_service.NewMo(i.code, i.product_name, i.quantity,
                         i.required_production_sec, i.pcs_per_box)
        for i in body.items
    ]
    made = mo_service.create(db, items, uuid.UUID(actor.user_id))
    return [_mo_out(m) for m in made]


@router.post("/mos/submit-batch", response_model=OkOut)
def submit_batch(body: MoBatchIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Chốt NHIỀU lệnh được tích chọn trên Sổ lệnh.
    Một mã hỏng thì cả lô không lệnh nào được chốt."""
    actor.require_role(PLANNER)
    n = mo_service.submit_batch(db, codes=body.codes, actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"Đã chốt {n} lệnh — khoá cứng mã/SL/thời gian (§4A)")


@router.post("/mos/cancel-batch", response_model=OkOut)
def cancel_batch(body: MoCancelBatchIn, db: DbDep, actor: ActorDep) -> OkOut:
    """Huỷ NHIỀU lệnh với CÙNG một lý do — lý do vẫn bắt buộc (§2.3)."""
    actor.require_role(PLANNER)
    n = mo_service.cancel_batch(db, codes=body.codes, reason=body.reason,
                                actor_id=uuid.UUID(actor.user_id))
    return OkOut(message=f"Đã huỷ {n} lệnh")


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


@router.get("/mos", response_model=Page[MoOut])
def list_mos(db: DbDep, actor: ActorDep, page: PageDep,
             status: MoStatus | None = None,
             date_from: date | None = None,
             date_to: date | None = None) -> Page[MoOut]:
    """MỘT TRANG danh sách lệnh, mới nhất trước.

    `status` lọc theo trạng thái; `date_from`/`date_to` lọc theo NGÀY TẠO lệnh — đó
    là mốc duy nhất mọi lệnh đều có, kể cả lệnh còn nháp chưa xuống xưởng.

    Lọc phải ở SERVER vì danh sách đã phân trang: lọc ở FE thì nó chỉ lọc được mười
    dòng đang cầm, và con số tổng trên đầu bảng thành nói dối.

    Quyền y hệt `GET /mos/{code}`: chỉ-đọc và mọi phòng ban đều xem được trạm 4
    (§9b). Mở chi tiết mà khoá danh sách thì mới là chỗ khó hiểu.
    """
    actor.require_step(4, VIEW)
    if date_from and date_to and date_from > date_to:
        raise Invalid("Ngày bắt đầu sau ngày kết thúc")
    limit, offset = page
    loc = {"status": status, "date_from": date_from, "date_to": date_to}
    rows = mo_repo.list_mos(db, **loc, limit=limit, offset=offset)
    return Page[MoOut](items=[_mo_out(m) for m in rows],
                       total=mo_repo.count_mos(db, **loc))


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
