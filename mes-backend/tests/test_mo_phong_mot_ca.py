"""Mô phỏng một ca — đo thật thay vì ước lượng.

Chạy riêng, KHÔNG nằm trong lượt test thường:

    pytest -m mo_phong -s
    MES_MP_GIAY=120 pytest -m mo_phong -s     # mỗi chặng 120 giây

Vì sao chạy ở TỐC ĐỘ THẬT, không nén thời gian: thứ quyết định tỉ lệ dùng lại cache là
TTL 5 giây gặp nhịp hỏi 10/30 giây. Một máy hỏi mỗi 10 giây thì lượt nào cũng trượt,
TRỪ KHI có máy khác vừa hỏi trong 5 giây trước đó — nên con số phụ thuộc vào số máy và
độ lệch pha giữa chúng. Nén thời gian là đo mất đúng thứ cần đo.

CSDL riêng, có commit thật: mỗi "máy" là một phiên riêng, phải nhìn thấy dữ liệu người
khác vừa ghi. Phiên test thường rollback nên không dùng được.

Đo cái gì:
  · `read_cache` dùng lại được bao nhiêu phần trăm
  · bao nhiêu lượt xuống thẳng CSDL, ở hàm nào
  · mỗi lượt ghi làm bao nhiêu trạm bị đánh thức → suy ra tải nếu bỏ polling sang push
"""

from __future__ import annotations

import itertools
import os
import random
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass, field

import pytest
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import sessionmaker

from app.common import event_bus, read_cache
from app.modules.board import repository as board_repo
from app.modules.board import service as board_service

pytestmark = pytest.mark.mo_phong

SECONDS_PER_PHASE = int(os.getenv("MES_MP_GIAY", "60"))

STATION_TABLETS = 18
WALL_BOARDS = 2
PLANNER_SCREENS = 2

RUNNING_INTERVAL = 10.0
OVERVIEW_INTERVAL = 10.0
COUNTS_INTERVAL = 30.0

PHASES = (("ĐẦU CA", 30.0), ("GIỮA CA", 2.0))
"""(tên, số lượt ghi mỗi phút).

BE-PLAN §1: vài trăm lượt ghi mỗi ngày, đỉnh là Kho phát 100 lệnh trong vài phút đầu ca.
Giữa ca là quét lẻ tẻ qua sáu trạm cộng sổ sản lượng giờ.
"""


_code_counter = itertools.count(100_000)
_code_lock = threading.Lock()


def _next_code() -> str:
    """Mã MO phải là chữ M kèm ĐÚNG 6 chữ số — `scan.mocode` từ chối mọi dạng khác."""
    with _code_lock:
        return f"M{next(_code_counter):06d}"


@dataclass
class Stats:
    reads: int = 0
    errors: list[str] = field(default_factory=list)
    writes: int = 0
    queries: Counter = field(default_factory=Counter)
    events: Counter = field(default_factory=Counter)
    cache: dict = field(default_factory=dict)


@pytest.fixture(scope="module")
def factory(db_url: str) -> Iterator[tuple[sessionmaker, uuid.UUID]]:
    """CSDL riêng đã migrate, kèm một tài khoản đủ vai. Dữ liệu được COMMIT thật."""
    db_name = f"mes_mp_{uuid.uuid4().hex[:8]}"
    admin = create_engine(db_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{db_name}"'))

    url = make_url(db_url).set(database=db_name).render_as_string(hide_password=False)
    r = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "MES_DATABASE_URL": url,
             "MES_JWT_SECRET": "khoa-chi-dung-cho-test-" + "0" * 16},
        capture_output=True, text=True, timeout=180,
    )
    assert r.returncode == 0, r.stderr[-2000:]

    engine = create_engine(url, pool_size=20, max_overflow=10, pool_pre_ping=True)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    from app.common.security.permissions import ROLES
    from app.modules.auth.models import AppUser

    with Session() as s:
        u = AppUser(full_name="Mô phỏng", emp_code=f"MP{uuid.uuid4().hex[:6]}",
                    roles=list(ROLES))
        s.add(u)
        s.commit()
        actor_id = u.id

    try:
        yield Session, actor_id
    finally:
        engine.dispose()
        with admin.connect() as c:
            c.execute(text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
                           " WHERE datname = :ten"), {"ten": db_name})
            c.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        admin.dispose()


def _count_queries(stats: Stats, monkeypatch) -> None:
    """Bọc các hàm đọc của `board_repo` để đếm lượt thật sự xuống CSDL."""
    for repo_func in ("running_rows", "count_running", "queue_rows", "count_queue",
                "queue_counts", "at_station_rows", "count_at_station"):
        original = getattr(board_repo, repo_func)

        def counted(*a, _that=original, _ten=repo_func, **k):
            stats.queries[_ten] += 1
            return _that(*a, **k)

        monkeypatch.setattr(board_repo, repo_func, counted)


def _read_once(Session: sessionmaker, stats: Stats, key: str, build) -> None:
    """Đúng đường mà router đi: cache trước, trượt thì mới mở phiên CSDL."""
    try:
        with Session() as s:
            read_cache.cached(key, lambda: build(s))
        stats.reads += 1
    except Exception as e:  # pragma: no cover
        stats.errors.append(f"đọc {key}: {type(e).__name__}: {e}")


def _reader_thread(Session, stats, key, build, interval, stop) -> threading.Thread:
    def loop() -> None:
        time.sleep(random.uniform(0, interval))   # lệch pha như máy bật không cùng lúc
        while not stop.is_set():
            _read_once(Session, stats, key, build)
            stop.wait(interval)

    return threading.Thread(target=loop, daemon=True)


def _writer_thread(Session, actor_id, stats, per_minute, stop) -> threading.Thread:
    """Sinh lượt ghi THẬT: phát lệnh → Kho quét nhận → bàn giao → Setup quét nhận.

    Bốn bước này không cần QC hay chia chuyền, mà vẫn chạm trạm 0, 1 và 2 — đủ để đo
    cả `bump()` lẫn `mark_affected`.
    """
    from app.modules.mo import service as mo_service
    from app.modules.scan import service as scan_service
    from app.modules.warehouse_out import service as wh_out

    pause = 60.0 / per_minute

    def loop() -> None:
        done = 0
        while not stop.is_set():
            code = _next_code()
            try:
                with Session() as s:
                    mo_service.create(
                        s, [mo_service.NewMo(code, "Vỏ nhựa mô phỏng", 1000, 3600, 0)],
                        actor_id)
                    mo_service.submit(s, code, actor_id)
                stats.writes += 2
                for step in range(4):
                    if stop.is_set():
                        return
                    stop.wait(pause)
                    with Session() as s:
                        if step == 0:
                            scan_service.scan(s, raw=code, station=0, actor_id=actor_id)
                        elif step == 1:
                            wh_out.handover(s, code=code, actor_id=actor_id)
                        elif step == 2:
                            scan_service.scan(s, raw=code, station=1, actor_id=actor_id)
                        else:
                            scan_service.scan(s, raw=code, station=2, actor_id=actor_id)
                    stats.writes += 1
                done += 1
            except Exception as e:  # pragma: no cover
                stats.errors.append(f"ghi {code}: {type(e).__name__}: {e}")
                stop.wait(pause)

    return threading.Thread(target=loop, daemon=True)


def _run_phase(Session, actor_id, writes_per_minute: float, seconds: int, monkeypatch) -> Stats:
    stats = Stats()
    read_cache.clear()
    _count_queries(stats, monkeypatch)

    def count_event(station: int):
        return lambda _d: stats.events.update([station])

    unsubs = [event_bus.subscribe(f"station:{n}", count_event(n)) for n in range(6)]

    stop = threading.Event()
    workers = []
    for _ in range(STATION_TABLETS + WALL_BOARDS + PLANNER_SCREENS):
        workers.append(_reader_thread(Session, stats, "board:counts:None:None",
                            lambda s: board_service.station_counts(s),
                            COUNTS_INTERVAL, stop))
    for _ in range(WALL_BOARDS):
        workers.append(_reader_thread(Session, stats, "board:running:10:0",
                            lambda s: board_service.running_board(s, limit=10, offset=0),
                            RUNNING_INTERVAL, stop))
    for _ in range(PLANNER_SCREENS):
        workers.append(_reader_thread(Session, stats, "board:overview",
                            lambda s: board_service.overview(s),
                            OVERVIEW_INTERVAL, stop))

    # Nhịp ghi chia cho số "người quét" chạy song song, mỗi người một chuỗi lệnh.
    writer_count = max(1, min(6, round(writes_per_minute / 5)))
    for _ in range(writer_count):
        workers.append(_writer_thread(
            Session, actor_id, stats, writes_per_minute / writer_count, stop))

    for t in workers:
        t.start()
    time.sleep(seconds)
    stop.set()
    for t in workers:
        t.join(timeout=15)
    for h in unsubs:
        h()

    stats.cache = read_cache.stats()
    return stats


def _print_report(phase_name: str, writes_per_minute: float, seconds: int, stats: Stats) -> None:
    c = stats.cache
    minutes = seconds / 60.0
    total_clients = STATION_TABLETS + WALL_BOARDS + PLANNER_SCREENS
    events = sum(stats.events.values())

    print(f"\n{'=' * 74}")
    print(f"{phase_name}  —  {writes_per_minute:.0f} lượt ghi/phút quy đổi, {seconds}s, "
          f"{total_clients} máy")
    print("=" * 74)
    print(f"  Lượt đọc phục vụ      : {stats.reads:>6}   ({stats.reads / minutes:.0f}/phút)")
    print(f"  Lượt ghi thật         : {stats.writes:>6}   ({stats.writes / minutes:.1f}/phút)")
    print(f"  Cache dùng lại được   : {c['hits']:>6}   ({(c['hit_rate'] or 0) * 100:.1f}%)")
    print(f"  Phải dựng lại         : {c['misses']:>6}")
    print(f"  Chờ lượt dựng của máy khác: {c['waits']:>2}   "
          f"(chống dồn đã gộp {c['waits']} lượt truy vấn)")
    print(f"  Số mục cache đang giữ : {c['keys']:>6}")

    print("\n  Truy vấn THẬT xuống CSDL:")
    for func_name, n in sorted(stats.queries.items(), key=lambda kv: -kv[1]):
        print(f"      {func_name:<20} {n:>6}   ({n / minutes:.1f}/phút)")
    total_queries = sum(stats.queries.values())
    print(f"      {'TỔNG':<20} {total_queries:>6}   ({total_queries / minutes:.1f}/phút)")
    if stats.reads:
        print(f"      → {total_queries / stats.reads:.2f} truy vấn mỗi lượt đọc "
              f"(không cache sẽ là ~2)")

    print("\n  Sự kiện đẩy tới từng trạm:")
    for n in range(6):
        print(f"      trạm {n}: {stats.events.get(n, 0):>5}")
    print(f"      TỔNG   : {events:>5}   ({events / minutes:.1f}/phút)")

    print("\nQuy đổi sang đường ĐẨY, kiểu 'báo có đổi rồi tự đi lấy':")
    tablets_per_station = STATION_TABLETS / 6
    if events:
        station_refetches = events * tablets_per_station / minutes
        print(f"      theo TRẠM (đang chạy): {events / minutes:.0f} sự kiện/phút"
              f" × {tablets_per_station:.0f} tablet/trạm  ≈  {station_refetches:.0f} req/phút")
    board_refetches = stats.writes * total_clients / minutes
    print(f"      theo BẢNG (việc 12)  : {stats.writes / minutes:.0f} lượt ghi/phút"
          f" × {total_clients} máy        ≈  {board_refetches:.0f} req/phút")
    print(f"      polling hiện tại     : {stats.reads / minutes:.0f} req/phút")

    if stats.errors:
        print(f"\n  LỖI ({len(stats.errors)}):")
        for e in stats.errors[:5]:
            print(f"      {e}")


def test_mo_phong_mot_ca(factory, monkeypatch, capsys):
    Session, actor_id = factory

    with capsys.disabled():
        print(f"\nMô phỏng {len(PHASES)} chặng × {SECONDS_PER_PHASE}s "
              f"(đổi bằng MES_MP_GIAY)")
        for phase_name, writes_per_minute in PHASES:
            stats = _run_phase(Session, actor_id, writes_per_minute, SECONDS_PER_PHASE, monkeypatch)
            _print_report(phase_name, writes_per_minute, SECONDS_PER_PHASE, stats)

            assert not stats.errors, f"{phase_name}: {stats.errors[:3]}"
            assert stats.reads > 0, f"{phase_name}: không có lượt đọc nào"
            assert stats.writes > 0, f"{phase_name}: không có lượt ghi nào"
            assert sum(stats.events.values()) > 0, (
                f"{phase_name}: ghi rồi mà KHÔNG trạm nào được báo — đường đẩy lại hỏng"
            )
            assert sum(stats.queries.values()) < stats.reads * 2, (
                f"{phase_name}: cache không đỡ được gì — {sum(stats.queries.values())} truy vấn "
                f"cho {stats.reads} lượt đọc"
            )
