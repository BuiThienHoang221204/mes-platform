"""Nền chung cho mọi bảng: Base · khoá chính UUID · bốn kiểu ENUM.

`Base` làm hai việc: cho model kế thừa để thành bảng, và giữ `Base.metadata` — sổ
liệt kê bảng.

Đừng dựa vào `Base.metadata` để biết hệ thống có những bảng nào: nó chỉ chứa bảng
của những file model ĐÃ được import, nên số lượng đổi theo chỗ gọi. Nguồn sự thật
về lược đồ là `app/db/migrations/versions/` — Alembic ở đây không so bằng metadata
(xem `migrations/env.py`).
"""

from __future__ import annotations

import uuid

from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.common.vocab.enums import MoStatus, QcVerdict, ReasonGroup, SegmentKind


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


# create_type=False: kiểu ENUM do migration tạo, model chỉ tham chiếu.
mo_status_enum = ENUM(MoStatus, name="mo_status", create_type=False)
qc_verdict_enum = ENUM(QcVerdict, name="qc_verdict", create_type=False)
segment_kind_enum = ENUM(SegmentKind, name="segment_kind", create_type=False)
reason_group_enum = ENUM(ReasonGroup, name="reason_group", create_type=False)
