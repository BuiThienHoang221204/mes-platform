"""Luật nghiệp vụ của màn Báo cáo sản xuất.

Chỉ đọc, nên không có ranh giới giao dịch nào ở đây. Việc của file này là CHẶN ĐẦU
VÀO và dựng lại hình dạng câu trả lời — hai việc không thuộc về repository.

Chặn đầu vào không phải thủ tục: khoá của `read_cache` ghép từ chính tham số client
gửi lên, mà kho cache là một `dict` không giới hạn. Không chặn miền giá trị thì gọi
mười nghìn lần với mười nghìn khoảng ngày khác nhau là mười nghìn mục nằm lại trong
bộ nhớ — chưa kể mỗi lần là một lượt quét bảng.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.common.clock import factory_tz
from app.common.config import settings
from app.common.errors import Invalid
from app.modules.reports import repository as reports_repo
from app.modules.reports import shift
from app.modules.reports.schemas import HourlyOut, HourlyPoint, HourlySeries, ShiftOut


def mo_progress(db: Session, *, status: str | None, limit: int, offset: int = 0,
                date_from: date | None = None, date_to: date | None = None) -> dict:
    """MỘT TRANG tiến độ lệnh, kèm tổng để màn hình biết còn trang sau không.

    `limit` kẹp thêm một lần nữa theo `report.max_rows`: `PageDep` đã kẹp ở cửa, nhưng
    service còn được gọi thẳng từ test và từ công cụ, không qua router.

    Ngày lọc theo `created_at` quy về giờ địa phương — cùng một định nghĩa với bộ lọc
    "Ngày tạo lệnh" của Sổ lệnh, không thì hai màn đếm ra hai con số khác nhau.
    """
    if date_from and date_to:
        _check_order(date_from, date_to)
    return {
        "items": reports_repo.mo_progress_rows(
            db, status=status,
            limit=max(1, min(limit, settings.report.max_rows)), offset=max(0, offset),
            date_from=date_from, date_to=date_to),
        "total": reports_repo.count_mo_progress(
            db, status=status, date_from=date_from, date_to=date_to),
    }


def _check_order(date_from: date, date_to: date) -> None:
    if date_from > date_to:
        raise Invalid("Ngày bắt đầu sau ngày kết thúc")


def _check_range(date_from: date, date_to: date) -> None:
    """Thêm trần độ dài, CHỈ cho báo cáo sản lượng giờ.

    Chỗ đó quét `hourly_output` theo từng ngày nên chi phí tăng theo số ngày xin.
    Tiến độ lệnh thì không: nó lọc `created_at` rồi `LIMIT`, 80 ngày tốn đúng
    bằng 1 ngày — đem trần này sang đó là chặn một câu hỏi hợp lệ mà không được gì.
    """
    _check_order(date_from, date_to)
    r = settings.report
    days = (date_to - date_from).days + 1
    if days > r.max_days:
        raise Invalid(f"Khoảng xem {days} ngày, quá {r.max_days} ngày cho phép — chia nhỏ ra")


def _check_codes(codes: list[str] | None) -> list[str] | None:
    if not codes:
        return None
    r = settings.report
    if len(codes) > r.max_codes:
        raise Invalid(f"Lọc {len(codes)} mã lệnh, quá {r.max_codes} mã cho phép")
    return sorted(set(codes))


def _check_bucket(bucket: int) -> int:
    if bucket not in shift.BUCKETS:
        hop_le = " · ".join(str(b) for b in shift.BUCKETS)
        raise Invalid(f"Khung gộp {bucket} giờ không có — chỉ nhận {hop_le}")
    return bucket


def hourly(
    db: Session,
    *,
    bucket: int,
    date_from: date,
    date_to: date,
    codes: list[str] | None,
) -> HourlyOut:
    """Sản lượng giờ theo khung, mỗi lệnh một chuỗi.

    Trả `at_end` chứ không bắt FE tự suy: khung cuối ca ngắn hơn các khung khác
    (`24 = 9 + 9 + 6` nếu gộp cả ngày), vẽ nó dài bằng khung kia là nói dối. Giờ
    kết thúc tra từ đúng danh sách khung mà câu SQL đã dùng để gộp.
    """
    bucket = _check_bucket(bucket)
    _check_range(date_from, date_to)
    codes = _check_codes(codes)

    rows = reports_repo.hourly_rows(
        db, bucket=bucket, date_from=date_from, date_to=date_to, codes=codes
    )

    end_of = dict(shift.bins_of(bucket))
    diem: dict[str, list[HourlyPoint]] = {}
    skipped = folded = 0

    for r in rows:
        skipped, folded = r["skipped_rows"], r["folded_rows"]
        if r["code"] is None:
            continue
        at: datetime = r["at"]
        if at.tzinfo is None:
            at = at.replace(tzinfo=factory_tz)
        diem.setdefault(r["code"], []).append(
            HourlyPoint(
                at=at,
                at_end=at + timedelta(hours=end_of[at.hour] - at.hour),
                qty=r["qty"],
                target_qty=r["target_qty"],
                headcount=r["headcount"],
                slots=r["slots"],
            )
        )

    return HourlyOut(
        bucket=bucket,
        target_pct=settings.report.target_pct,
        shift=ShiftOut.current(),
        series=[HourlySeries(code=c, points=p) for c, p in sorted(diem.items())],
        skipped_rows=skipped,
        folded_rows=folded,
    )
