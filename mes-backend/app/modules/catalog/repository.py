"""Truy vấn hai danh mục `line` và `reason_code`.

    get_line(db, code)                     ném lỗi nếu không có chuyền
    list_lines(db)                         cả chuyền đã tắt — màn hình quản trị cần
    create_line(db, code, name)            thêm chuyền, tự cấp `id` kế tiếp
    delete_line(db, code)                  CHỈ xoá được chuyền chưa ai dùng
    list_reasons(db, group=None)           CHỈ dòng còn is_active

`list_reasons` lọc `is_active` vì lý do bỏ đi vẫn phải giữ trong bảng (bản ghi cũ
còn trỏ tới) nhưng không được hiện lên ô chọn nữa.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.errors import NotFound
from app.modules.catalog.models import Line, ReasonCode


def get_line(db: Session, code: str) -> Line:
    """Tra chuyền theo mã `L01`. NÉM lỗi nếu không có — gán chuyền không tồn tại là sai."""
    line = db.scalar(select(Line).where(Line.code == code))
    if line is None:
        raise NotFound(f"Không có chuyền {code}")
    return line


def list_lines(db: Session) -> list[Line]:
    """Trả CẢ chuyền đã tắt — màn hình quản trị cần thấy để bật lại."""
    return list(db.scalars(select(Line).order_by(Line.id)))


def create_line(db: Session, *, code: str, name: str | None = None) -> Line:
    """Thêm một chuyền. Tự tính `id` kế tiếp vì `line.id` là smallint trần, không tự tăng.

    Hai người thêm cùng lúc thì người sau đụng khoá chính — hỏng rõ, không sinh id trùng.
    """
    next_id = (db.scalar(select(func.max(Line.id))) or 0) + 1
    line = Line(id=next_id, code=code, name=name)
    db.add(line)
    return line


def delete_line(db: Session, code: str) -> None:
    """Xoá hẳn một chuyền — chỉ được khi chuyền chưa từng chạy MO nào.

    Chuyền đã có lịch sử thì khoá ngoại `line_segment` chặn; muốn nghỉ thì tắt `is_active`.
    """
    db.delete(get_line(db, code))


def list_reasons(db: Session, group: str | None = None) -> list[ReasonCode]:
    """`group` để FE chỉ lấy đúng nhóm lý do của ô đang mở.

    Chỉ trả dòng còn `is_active`: lý do bỏ đi vẫn phải giữ trong bảng vì các
    bản ghi cũ còn trỏ tới, nhưng không được hiện lên ô chọn nữa.
    """
    stmt = select(ReasonCode).where(ReasonCode.is_active.is_(True))
    if group:
        stmt = stmt.where(ReasonCode.group_code == group)
    return list(db.scalars(stmt.order_by(ReasonCode.group_code, ReasonCode.name)))
