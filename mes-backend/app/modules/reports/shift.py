"""Chia khung giờ theo GIỜ ĐI LÀM — nguồn DUY NHẤT, cả SQL lẫn Python đọc từ đây.

    bins_of(1)  →  [(6,7), (7,8), … (20,21), (21,22)]      16 khung, trải cả ngày
    bins_of(4)  →  [(8,12), (13,17)]                        hai buổi
    bins_of(9)  →  [(8,17)]                                 cả ca

Khung 1 giờ KHÔNG cắt theo giờ đi làm: mỗi giờ một ô thì không ô nào đụng ô nào,
nên giờ tăng ca hiện nguyên hình. Khung gom thì ngược lại — một khung ôm giờ nghỉ
trưa sẽ tụt oan, nên nó cắt theo buổi. Lý lẽ đầy đủ ở `KE-HOACH-BAO-CAO-SAN-XUAT.md` §3.5.

Repository dựng biểu thức SQL gộp khung TỪ danh sách này chứ không viết tay `CASE`
song song. Viết tay hai bản thì đổi giờ làm là hai bản trôi khỏi nhau mà không test
nào đỏ — đúng loại lỗi chỉ lộ ra khi có người hỏi "sao báo cáo lệch sổ".
"""

from __future__ import annotations

from app.common.config import settings

Bin = tuple[int, int]

BUCKETS: tuple[int, ...] = (1, 4, settings.report.shift_span)


def bins_of(bucket: int) -> list[Bin]:
    """Các khung `[giờ bắt đầu, giờ kết thúc)` của một mức gộp, theo thứ tự thời gian."""
    r = settings.report
    if bucket >= r.shift_span:
        return [(r.shift_start, r.shift_end)]
    if bucket == 1:
        return [(h, h + 1) for h in range(r.day_start, r.day_end)]
    out: list[Bin] = []
    for start, end in ((r.shift_start, r.lunch_start), (r.lunch_end, r.shift_end)):
        out += [(h, min(h + bucket, end)) for h in range(start, end, bucket)]
    return out


def bin_of(hour: int, bucket: int) -> int:
    """Giờ thô rơi vào khung nào — trả về giờ BẮT ĐẦU của khung đó.

    Giờ nằm ngoài mọi khung (tăng ca, hoặc trưa không nghỉ) ghép vào khung gần
    nhất về phía trước. KHÔNG bỏ đi: bỏ thì tổng trên màn hình khác tổng trong sổ,
    lỗi nặng hơn nhiều so với nhãn khung hơi rộng.
    """
    bins = bins_of(bucket)
    pick = bins[0][0]
    for start, _ in bins:
        if hour >= start:
            pick = start
    return pick


def is_folded(hour: int, bucket: int) -> bool:
    """Dòng này có bị đẩy sang khung khác với giờ thật của nó không."""
    return not any(start <= hour < end for start, end in bins_of(bucket))


def merged_ranges(bucket: int) -> list[Bin]:
    """Gộp các khung liền nhau thành khoảng lớn — dùng dựng vế `NOT (…)` cho gọn."""
    out: list[Bin] = []
    for start, end in bins_of(bucket):
        if out and out[-1][1] == start:
            out[-1] = (out[-1][0], end)
        else:
            out.append((start, end))
    return out
