"""Nạp dữ liệu mẫu cho máy phát triển — đủ mọi tình huống của quy trình.

    ./run.sh seed-demo              nạp thêm
    ./run.sh seed-demo --wipe       xoá lệnh mẫu cũ rồi nạp lại
    ./run.sh seed-demo --wipe-only  chỉ dọn, không nạp

**Đi qua SERVICE chứ không INSERT thẳng.** Mọi ràng buộc, trigger và bản ghi nhật ký
đều chạy y như lúc người thật bấm nút, nên dữ liệu ra KHÔNG thể ở trạng thái mà ứng
dụng không tạo nổi. Nhồi bằng SQL thô thì nhanh hơn nhiều, nhưng rồi màn hình hiện
những tổ hợp không bao giờ xảy ra ngoài xưởng và người ta đi sửa những lỗi không có thật.

**Mã lệnh mẫu đều bắt đầu bằng `M2`** (`M200001`…). Nhờ vậy `--wipe` dọn đúng phần
mình tạo, không đụng lệnh thật ai đang thử.

Ngoại lệ DUY NHẤT không đi qua service: vài dòng sản lượng giờ thiếu `target_qty`.
Cột đó thêm ở migration `0006` nên dữ liệu cũ hơn không có, mà service bây giờ bắt
buộc phải khai — không dựng được bằng đường thường. Nó là thứ duy nhất làm màn báo
cáo hiện dòng "đã bỏ n dòng chưa khai sản lượng yêu cầu".
"""

from __future__ import annotations

import argparse
import random
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.common.config import settings  # noqa: E402
from app.common.vocab.enums import QcVerdict  # noqa: E402
from app.modules.mo import service as mo_service  # noqa: E402
from app.modules.packing import hourly_service as pack_hourly_service  # noqa: E402
from app.modules.packing import service as packing_service  # noqa: E402
from app.modules.production import hourly_service  # noqa: E402
from app.modules.production import service as production_service  # noqa: E402
from app.modules.qc import service as qc_service  # noqa: E402
from app.modules.round import service as round_service  # noqa: E402
from app.modules.round import step_service  # noqa: E402
from app.modules.warehouse_in import service as warehouse_in_service  # noqa: E402
from app.modules.warehouse_out import service as warehouse_out_service  # noqa: E402

PREFIX = "M2"
LINES = [f"L{i:02d}" for i in range(1, 15)]

PRODUCTS = [
    ("Vỏ hộp số F3", 12_000, 500),
    ("Niềng xe 17 inch", 9_000, 300),
    ("Chụp cáp N-type", 6_000, 250),
    ("Đầu nối SMA", 4_000, 200),
    ("Vòng đệm cao su", 15_000, 1_000),
    ("Ốc hãm M6", 2_500, 0),
    ("Giá đỡ ăng-ten", 7_500, 400),
    ("Nắp chụp BNC", 5_000, 250),
]

HOLD_REASONS = ["Hỏng khuôn", "Chờ vật tư", "Máy dừng bảo trì", "Kẹt phôi", "Mất điện"]
NG_REASONS = ["Lỗi kích thước", "Xước bề mặt", "Sai vật liệu"]
SHORT_REASONS = ["Thiếu vật tư", "Hết ca chưa xong", "Máy hỏng giữa chừng"]
QC_FAIL_REASONS = ["Sai dung sai", "Bavia chưa gọt", "Lệch tâm"]

class Seeder:
    """Đi lại đúng các bước mà người ở xưởng bấm, theo thứ tự."""

    def __init__(self, db: Session, rng: random.Random):
        self.db = db
        self.rng = rng
        self.users = {
            r[1]: r[0]
            for r in db.execute(text("SELECT id, emp_code FROM app_user")).all()
        }
        self.reasons = {
            r[0]: r[1]
            for r in db.execute(
                text("SELECT DISTINCT ON (group_code) group_code, id"
                     " FROM reason_code ORDER BY group_code, id")
            ).all()
        }
        self.n = 0

    def who(self, emp: str) -> uuid.UUID:
        """Người thao tác đúng phòng ban — để nhật ký đọc ra chuyện thật."""
        return self.users.get(emp) or next(iter(self.users.values()))

    def new_mo(self) -> tuple[str, int, int]:
        self.n += 1
        code = f"{PREFIX}{self.n:05d}"
        name, qty, box = self.rng.choice(PRODUCTS)
        minutes = self.rng.choice([120, 180, 240, 300])
        mo_service.create(
            self.db, [mo_service.NewMo(code, name, qty, minutes * 60, box)], self.who("NV001")
        )
        return code, qty, box

    def submit(self, code: str) -> None:
        mo_service.submit(self.db, code, self.who("NV001"))

    def accept(self, code: str, step: int, emp: str) -> None:
        _, rnd = round_service.lock_round(self.db, code)
        step_service.accept(self.db, rnd=rnd, step_no=step, actor_id=self.who(emp))

    def handover(self, code: str) -> None:
        warehouse_out_service.handover(self.db, code=code, actor_id=self.who("NV010"))

    def qc(self, code: str, ok: bool) -> None:
        qc_service.qc_decide(
            self.db, code=code,
            result=QcVerdict.PASS if ok else QcVerdict.FAIL,
            reason_code_id=None if ok else self.reasons.get("QC"),
            reason_text=None if ok else self.rng.choice(QC_FAIL_REASONS),
            actor_id=self.who("NV030"),
        )

    def assign(self, code: str, line: str) -> None:
        production_service.assign_line(
            self.db, code=code, line_code=line, actor_id=self.who("NV050"))

    def start(self, code: str, line: str) -> None:
        production_service.line_start(
            self.db, code=code, line_code=line, actor_id=self.who("NV050"))

    def hold(self, code: str, line: str) -> None:
        production_service.line_hold(
            self.db, code=code, line_code=line,
            reason_code_id=self.reasons.get("HOLD"),
            reason_text=self.rng.choice(HOLD_REASONS), actor_id=self.who("NV050"))

    def hourly(self, code: str, target: int, days: int = 3, fill: float = 0.8) -> int:
        """Ghi sổ sản lượng giờ nhiều ngày — nguồn của biểu đồ Năng suất theo giờ.

        **Ngày cuối LUÔN là HÔM NAY.** Trước đây hàm này đổ đầy từ ngày xa nhất rồi
        dừng ngay khi đủ số, nên phần lớn lệnh không có dòng nào của hôm nay — màn
        báo cáo mặc định xem hôm nay thì trắng trơn. Giờ chia hạn mức cho từng ngày
        trước, nên ngày nào cũng có số và hôm nay chắc chắn có.

        Giờ tăng ca (6, 7, 17, 18) cố ý có mặt: đó là thứ làm khung gom hiện dòng
        "n dòng ghi ngoài giờ đi làm". Không có nó thì nhánh ấy không bao giờ chạy.
        """
        room = int(target * fill)
        if room <= 0:
            return 0

        span = max(1, days)
        dates = [date.today() - timedelta(days=span - 1 - i) for i in range(span)]
        share = [room // span] * span
        share[-1] += room - sum(share)

        hours = [8, 9, 10, 11, 13, 14, 15, 16]
        strict = fill >= 1.0
        made = 0

        for work_date, quota in zip(dates, share, strict=True):
            left = quota
            slots = list(hours)
            if self.rng.random() < 0.45:
                slots += self.rng.sample([6, 7, 17, 18], k=self.rng.randint(1, 2))
            slots = sorted(slots)
            used: set[int] = set()
            for i, slot in enumerate(slots):
                if left <= 0:
                    break
                if not strict and i and self.rng.random() < 0.15:
                    continue
                people = self.rng.randint(6, 14)
                want = people * self.rng.randint(45, 70)
                # Ba mức để biểu đồ có đủ đỏ / xanh dương / xanh lá, không phải một màu.
                ratio = self.rng.choice([
                    self.rng.uniform(0.55, 0.84),
                    self.rng.uniform(0.86, 0.99),
                    self.rng.uniform(1.01, 1.25),
                ])
                got = max(1, min(int(want * ratio), left))
                hourly_service.add_hourly(
                    self.db, code=code, work_date=work_date, slot_hour=slot,
                    headcount=people, target_qty=want, qty=got,
                    note=self.rng.choice(HOLD_REASONS) if got < want * 0.85 else None,
                    actor_id=self.who("NV050"),
                )
                used.add(slot)
                left -= got
                made += got
            if strict and left > 0:
                made += self._top_up(code, work_date, left, used)
        return made

    def _top_up(self, code: str, work_date: date, left: int, used: set[int]) -> int:
        """Đổ nốt phần còn thiếu vào một khung CHƯA DÙNG của chính ngày đó.

        `UNIQUE (round_id, work_date, slot_hour)` cấm hai dòng cùng một khung, nên
        phải chọn khung trống chứ không cộng thêm vào khung đã ghi.
        """
        for slot in (19, 20, 21, 5, 22):
            if slot in used:
                continue
            hourly_service.add_hourly(
                self.db, code=code, work_date=work_date, slot_hour=slot,
                headcount=self.rng.randint(6, 12), target_qty=max(1, left), qty=left,
                note="Bù cuối ca", actor_id=self.who("NV050"),
            )
            return left
        return 0

    def close_book(self, code: str, target: int, made: int) -> int:
        """Ba số phải cộng đúng bằng mục tiêu vòng (§7.5) — trigger kiểm lại."""
        ok = made if made else int(target * 0.9)
        rest = target - ok
        ng = min(rest, int(target * self.rng.uniform(0, 0.04)))
        short = rest - ng
        production_service.close_production(
            self.db, code=code, qty_ok=ok, qty_ng=ng, qty_short=short,
            ng_reason_code_id=self.reasons.get("NG") if ng else None,
            ng_reason_text=self.rng.choice(NG_REASONS) if ng else None,
            short_reason_code_id=self.reasons.get("SHORT") if short else None,
            short_reason_text=self.rng.choice(SHORT_REASONS) if short else None,
            actor_id=self.who("NV050"),
        )
        return ok

    def pack_boxes(self, code: str, box: int, ok: int, days: int = 2) -> None:
        """Đếm thùng theo giờ — ngày cuối luôn là hôm nay, cùng lý do với `hourly`."""
        packing_service.packing_start(self.db, code=code, actor_id=self.who("NV060"))
        if not box:
            return
        left = ok // box
        span = max(1, days)
        for i in range(span):
            work_date = date.today() - timedelta(days=span - 1 - i)
            for slot in (9, 11, 14, 16):
                if left <= 0:
                    return
                n = min(left, self.rng.randint(1, 4))
                pack_hourly_service.add_packing_hourly(
                    self.db, code=code, work_date=work_date, slot_hour=slot,
                    boxes=n, note=None, actor_id=self.who("NV060"))
                left -= n

    def pack_finish(self, code: str, ok: int) -> None:
        packing_service.packing_finish(
            self.db, code=code, qty_packed=ok, note_text="Đủ", actor_id=self.who("NV060"))

    def warehouse_in(self, code: str) -> None:
        warehouse_in_service.complete(
            self.db, code=code, qty_received=None, actor_id=self.who("NV070"))

    def round_target(self, code: str) -> int:
        """Mục tiêu của VÒNG ĐANG MỞ — vòng hai chỉ còn phần thiếu, không phải cả đơn."""
        return self.db.execute(text(
            "SELECT r.target_qty FROM mo_round r"
            " JOIN manufacturing_order m ON m.id = r.mo_id"
            " WHERE m.code = :c AND r.closed_at IS NULL"), {"c": code}).scalar() or 0

    def full_round(self, code: str, line: str, box: int, days: int = 2) -> int:
        """Một vòng chạy trọn: chia chuyền → ghi sổ đủ → chốt → đóng thùng → nhập kho."""
        self.assign(code, line)
        self.start(code, line)
        target = self.round_target(code)
        made = self.hourly(code, target, days=days, fill=1.0)
        ok = self.close_book(code, target, made)
        self.pack_boxes(code, box, ok)
        self.pack_finish(code, ok)
        self.accept(code, 5, "NV070")
        self.warehouse_in(code)
        return ok

    def next_round_from(self, code: str, step: int, emp: str) -> None:
        """Vòng mới đã tự mở khi chốt vòng trước — chỉ cần nhận ở bước nó quay về.

        QC không đạt thì vòng sau bắt đầu từ bước 0 (§6b.1); thiếu số ở Kho nhập
        thì bắt đầu từ bước 3 (§6b.2). Hai đường về khác nhau, nên phải nói rõ bước.
        """
        if step == 0:
            self.ready_for(code, 4)
        self.accept(code, step, emp)

    def part_round(self, code: str, line: str, box: int, fill: float, days: int = 2) -> int:
        """Một vòng chạy KHÔNG ĐỦ — đi trọn tới Kho nhập để vòng sau tự mở."""
        self.assign(code, line)
        self.start(code, line)
        target = self.round_target(code)
        made = self.hourly(code, target, days=days, fill=fill)
        ok = self.close_book(code, target, made)
        self.pack_boxes(code, box, ok)
        self.pack_finish(code, ok)
        self.accept(code, 5, "NV070")
        self.warehouse_in(code)
        return ok

    def cancel(self, code: str) -> None:
        mo_service.cancel(self.db, code, "Khách huỷ đơn", self.who("NV001"))

    def ready_for(self, code: str, step: int) -> None:
        """Chạy mọi bước đứng trước, để lệnh nằm đúng HÀNG ĐỢI của `step`.

        Muốn nó nằm TRONG TAY trạm thì gọi thêm `accept(code, step, …)`. Tách hai
        việc vì đó đúng là hai trạng thái khác nhau trên màn hình trạm.
        """
        if step >= 1:
            self.accept(code, 0, "NV010")
            self.handover(code)
        if step >= 2:
            self.accept(code, 1, "NV020")
        if step >= 3:
            self.accept(code, 2, "NV030")
            self.qc(code, ok=True)
        if step >= 4:
            self.accept(code, 3, "NV040")

def wipe(db: Session) -> int:
    """Xoá lệnh mẫu — và phải tự tắt lá chắn của nhật ký mới xoá được.

    `mo_event` là sổ CHỈ GHI THÊM: hai RULE `mo_event_no_update` và `mo_event_no_delete`
    biến mọi lệnh sửa/xoá thành `DO INSTEAD NOTHING`. Đúng thiết kế — nhật ký sửa được
    thì không còn là nhật ký nữa.

    Điều đáng biết: RULE **không báo lỗi**, nó nuốt câu lệnh rồi báo "đã xoá 0 dòng".
    Lần đầu chạy hàm này, `DELETE FROM mo_event` đi qua êm ru — chỉ tới lúc `DELETE
    FROM mo_round` đụng khoá ngoại mới lộ ra là không có gì bị xoá cả.

    Tắt RULE ở đây là việc của công cụ DÀNH RIÊNG CHO MÁY PHÁT TRIỂN, và chỉ để dọn
    đúng phần mình tạo (mã `M2…`). `finally` bật lại kể cả khi giữa chừng hỏng.
    """
    like = f"{PREFIX}%"
    ids = [r[0] for r in db.execute(
        text("SELECT id FROM manufacturing_order WHERE code LIKE :p"), {"p": like}).all()]
    if not ids:
        return 0
    db.execute(text("ALTER TABLE mo_event DISABLE RULE mo_event_no_delete"))
    try:
        db.execute(text(
            "DELETE FROM mo_event WHERE mo_id = ANY(:i)"
            " OR round_id IN (SELECT id FROM mo_round WHERE mo_id = ANY(:i))"), {"i": ids})
        db.execute(text("DELETE FROM mo_round WHERE mo_id = ANY(:i)"), {"i": ids})
        db.execute(text("DELETE FROM manufacturing_order WHERE id = ANY(:i)"), {"i": ids})
    finally:
        db.execute(text("ALTER TABLE mo_event ENABLE RULE mo_event_no_delete"))
        db.commit()
    return len(ids)

def legacy_hourly_rows(db: Session, codes: list[str]) -> int:
    """Dòng sản lượng giờ THIẾU `target_qty` — dữ liệu từ trước migration `0006`.

    Service bây giờ bắt buộc khai định mức nên không dựng được bằng đường thường.
    Đây là thứ duy nhất làm màn báo cáo hiện dòng "đã bỏ n dòng chưa khai…".
    """
    made = 0
    for code in codes:
        row = db.execute(text(
            "SELECT r.id FROM mo_round r JOIN manufacturing_order m ON m.id = r.mo_id"
            " WHERE m.code = :c ORDER BY r.round_no DESC LIMIT 1"), {"c": code}).first()
        if row is None:
            continue
        db.execute(text(
            "INSERT INTO hourly_output (id, round_id, work_date, slot_hour, headcount,"
            "                           target_qty, qty, recorded_by)"
            " VALUES (:i, :r, :d, 12, 8, NULL, 220,"
            "         (SELECT id FROM app_user WHERE emp_code = 'NV050'))"
            " ON CONFLICT DO NOTHING"),
            {"i": uuid.uuid4(), "r": row[0], "d": date.today()})
        made += 1
    db.commit()
    return made

def build(s: Seeder) -> dict[str, int]:
    rng = s.rng
    done: dict[str, int] = {}
    ran: list[str] = []

    def tally(name: str) -> None:
        done[name] = done.get(name, 0) + 1

    for _ in range(3):
        s.new_mo()
        tally("Nháp, chưa Submit")

    for step, n_queue, n_at, emp in (
        (0, 6, 4, "NV010"), (1, 4, 4, "NV020"), (2, 4, 4, "NV030"),
        (3, 4, 3, "NV040"), (4, 3, 0, "NV050"),
    ):
        for _ in range(n_queue):
            code, _, _ = s.new_mo()
            s.submit(code)
            s.ready_for(code, step)
            tally(f"Chờ nhận ở bước {step}")
        for _ in range(n_at):
            code, _, _ = s.new_mo()
            s.submit(code)
            s.ready_for(code, step)
            s.accept(code, step, emp)
            if step == 2:
                pass  # QC đã nhận nhưng CHƯA ra kết quả — nút Ra kết quả còn bật
            tally(f"Đang ở bước {step}")

    for _ in range(3):
        code, _, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 2)
        s.accept(code, 2, "NV030")
        s.qc(code, ok=False)
        tally("QC Không đạt, sang vòng 2")

    for i in range(4):
        code, _, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        s.assign(code, LINES[i % len(LINES)])
        tally("Đã chia chuyền, chưa chạy")

    for i in range(10):
        code, qty, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[i % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        s.hourly(code, qty, days=rng.randint(1, 3))
        ran.append(code)
        tally("Đang lắp ráp")

    for i in range(3):
        code, qty, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 5) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        s.hourly(code, qty, days=1)
        s.hold(code, line)
        ran.append(code)
        tally("Chuyền đang dừng, có lý do")

    for i in range(4):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 2) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2)
        s.close_book(code, qty, made)
        ran.append(code)
        tally("Đã chốt sổ, chưa đóng thùng")

    for i in range(3):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 7) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok)
        ran.append(code)
        tally("Đang đóng thùng")

    for i in range(3):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 9) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok)
        s.pack_finish(code, ok)
        ran.append(code)
        tally("Đóng thùng xong, chờ Kho nhập")

    for i in range(3):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 11) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok)
        s.pack_finish(code, ok)
        s.accept(code, 5, "NV070")
        ran.append(code)
        tally("Kho nhập đã nhận, chưa xác nhận")

    for i in range(6):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        s.full_round(code, LINES[(i + 3) % len(LINES)], box, days=3)
        ran.append(code)
        tally("Xong đơn ngay vòng 1")

    for i in range(4):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 6) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2, fill=0.6)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok)
        s.pack_finish(code, ok)
        s.accept(code, 5, "NV070")
        s.warehouse_in(code)
        s.accept(code, 4, "NV050")
        s.full_round(code, line, box, days=2)
        ran.append(code)
        tally("Thiếu ở vòng 1, xong ở vòng 2")

    for i in range(4):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 12) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=2, fill=0.55)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok)
        s.pack_finish(code, ok)
        s.accept(code, 5, "NV070")
        s.warehouse_in(code)
        ran.append(code)
        tally("Thiếu, đang chờ chạy vòng 2")

    for i in range(3):
        code, _, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 4) % len(LINES)]
        s.part_round(code, line, box, fill=0.35)
        s.next_round_from(code, 3, "NV040")
        s.accept(code, 4, "NV050")
        s.part_round(code, LINES[(i + 8) % len(LINES)], box, fill=0.5)
        s.next_round_from(code, 3, "NV040")
        s.accept(code, 4, "NV050")
        s.full_round(code, LINES[(i + 1) % len(LINES)], box, days=2)
        ran.append(code)
        tally("Phải chạy tới VÒNG 3 mới đủ")

    for i in range(3):
        code, _, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 2)
        s.accept(code, 2, "NV030")
        s.qc(code, ok=False)
        s.next_round_from(code, 0, "NV010")
        s.accept(code, 4, "NV050")
        s.full_round(code, LINES[(i + 10) % len(LINES)], box, days=2)
        ran.append(code)
        tally("QC trả về, vòng 2 chạy xong")

    for i in range(3):
        code, _, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        s.part_round(code, LINES[(i + 13) % len(LINES)], box, fill=0.45)
        s.next_round_from(code, 3, "NV040")
        ran.append(code)
        tally("Kho nhập trả lại, đang ở Bàn team leader")

    for i in range(3):
        code, qty, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        for k in range(3):
            line = LINES[(i * 3 + k) % len(LINES)]
            s.assign(code, line)
            s.start(code, line)
        s.hourly(code, qty, days=2, fill=0.5)
        ran.append(code)
        tally("Ba chuyền chạy song song")

    for i in range(2):
        code, qty, _ = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 6) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        s.hourly(code, qty, days=1, fill=0.3)
        ran.append(code)
        tally("Mới ghi sổ giờ HÔM NAY")

    for i in range(2):
        code, qty, box = s.new_mo()
        s.submit(code)
        s.ready_for(code, 4)
        s.accept(code, 4, "NV050")
        line = LINES[(i + 2) % len(LINES)]
        s.assign(code, line)
        s.start(code, line)
        made = s.hourly(code, qty, days=1, fill=0.9)
        ok = s.close_book(code, qty, made)
        s.pack_boxes(code, box, ok, days=1)
        ran.append(code)
        tally("Đóng thùng theo giờ HÔM NAY")

    for _ in range(2):
        code, _, _ = s.new_mo()
        s.submit(code)
        s.cancel(code)
        tally("Đã huỷ")

    done["_ran"] = len(ran)
    s.ran = ran  # type: ignore[attr-defined]
    return done

def main() -> None:
    ap = argparse.ArgumentParser(description="Nạp dữ liệu mẫu cho máy phát triển")
    ap.add_argument("--wipe", action="store_true", help="xoá lệnh mẫu cũ trước khi nạp")
    ap.add_argument("--wipe-only", action="store_true", help="chỉ dọn, không nạp")
    ap.add_argument("--seed", type=int, default=20260916, help="hạt ngẫu nhiên")
    args = ap.parse_args()

    engine = create_engine(settings.database.url)
    db = sessionmaker(bind=engine)()

    if args.wipe or args.wipe_only:
        print(f"đã xoá {wipe(db)} lệnh mẫu cũ")
    if args.wipe_only:
        return

    s = Seeder(db, random.Random(args.seed))
    done = build(s)
    ran = getattr(s, "ran", [])
    legacy = legacy_hourly_rows(db, ran[:3])

    print(f"\nĐã nạp {s.n} lệnh mã {PREFIX}00001…{PREFIX}{s.n:05d}\n")
    for name, n in done.items():
        if not name.startswith("_"):
            print(f"  {n:3}  {name}")
    print(f"\n  {legacy} dòng sản lượng giờ thiếu định mức (dữ liệu cũ trước 0006)")

    rows = db.execute(text(
        "SELECT status, count(*) FROM manufacturing_order WHERE code LIKE :p GROUP BY 1"
    ), {"p": f"{PREFIX}%"}).all()
    print("\n  trạng thái:", ", ".join(f"{r[0]} {r[1]}" for r in rows))
    print("  dòng sản lượng giờ:", db.execute(text(
        "SELECT count(*) FROM hourly_output h JOIN mo_round r ON r.id = h.round_id"
        " JOIN manufacturing_order m ON m.id = r.mo_id WHERE m.code LIKE :p"
    ), {"p": f"{PREFIX}%"}).scalar())
    db.close()

if __name__ == "__main__":
    main()
