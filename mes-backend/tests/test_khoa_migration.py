"""Hai tiến trình cùng `alembic upgrade head` phải XẾP HÀNG, không giành nhau.

Không có khoá thì cả hai đọc `alembic_version` thấy cùng một mốc, cùng chạy một
migration, và cái thứ hai gãy giữa chừng — có thể để lại lược đồ dở dang. Đó là lý do
BE-PLAN §10 phải cấm nhiều worker cùng migrate lúc khởi động.

Chạy bằng TIẾN TRÌNH con chứ không phải luồng: `alembic.context` là một proxy cấp
module, hai lượt chạy trong cùng tiến trình sẽ giẫm lên nhau và test hoá ra đo nhầm
thứ. Hai tiến trình con là đúng cảnh production.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, make_url, text

from app.db.migration_lock import MIGRATION_LOCK_KEY

# `pg_locks` là bảng TOÀN CỤM. Không lọc theo CSDL thì đếm nhầm khoá của ca test khác,
# và ca "đã nhả khoá chưa" sẽ đỏ vì lý do chẳng liên quan.
_COUNT_LOCKS = text(
    "SELECT count(*) FROM pg_locks"
    " WHERE locktype = 'advisory' AND objid = :lock_key"
    "   AND database = (SELECT oid FROM pg_database WHERE datname = current_database())"
)


@pytest.fixture
def empty_db(db_url: str) -> Iterator[str]:
    """Một CSDL rỗng, riêng cho ca này — migration phải chạy từ đầu mới có đua."""
    db_name = f"mes_dua_{uuid.uuid4().hex[:8]}"
    admin = create_engine(db_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{db_name}"'))
    try:
        # `str(URL)` che mật khẩu thành `***` — phải render tường minh.
        yield make_url(db_url).set(database=db_name).render_as_string(hide_password=False)
    finally:
        with admin.connect() as c:
            c.execute(text(
                "SELECT pg_terminate_backend(pid) FROM pg_stat_activity"
                " WHERE datname = :ten"), {"ten": db_name})
            c.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        admin.dispose()


def _run_alembic(url: str) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "MES_DATABASE_URL": url,
        "MES_JWT_SECRET": "khoa-chi-dung-cho-test-" + "0" * 16,
    }
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env=env, capture_output=True, text=True, timeout=180,
    )


def _count_locks(url: str) -> int:
    probe = create_engine(url, isolation_level="AUTOCOMMIT")
    try:
        with probe.connect() as c:
            return c.scalar(_COUNT_LOCKS, {"lock_key": MIGRATION_LOCK_KEY}) or 0
    finally:
        probe.dispose()


class _LockWatcher:
    """Theo dõi nền: có lúc nào khoá được ôm không, trong lúc migration đang chạy."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._stop = threading.Event()
        self.seen = False
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def _loop(self) -> None:
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline and not self._stop.is_set():
            try:
                if _count_locks(self._url):
                    self.seen = True
                    return
            except Exception:
                pass          # CSDL vừa bị đóng kết nối giữa chừng — thử lại
            time.sleep(0.02)

    def __enter__(self) -> _LockWatcher:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=5)


def test_hai_tien_trinh_cung_migrate_thi_ca_hai_deu_qua(empty_db: str):
    results: list[subprocess.CompletedProcess] = []

    def run() -> None:
        results.append(_run_alembic(empty_db))

    threads = [threading.Thread(target=run) for _ in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=240)

    assert len(results) == 2, "có tiến trình không kết thúc"
    for i, r in enumerate(results):
        assert r.returncode == 0, (
            f"tiến trình {i} gãy — đây chính là cảnh giành nhau `alembic_version`:\n"
            f"{r.stderr[-2000:]}"
        )


def test_khoa_thuc_su_duoc_om_trong_luc_migrate(empty_db: str):
    """Thiếu khẳng định này thì ca trên có thể xanh vì may, chứ không vì có khoá."""
    with _LockWatcher(empty_db) as watcher:
        r = _run_alembic(empty_db)

    assert r.returncode == 0, r.stderr[-2000:]
    assert watcher.seen, (
        "không thấy khoá tư vấn nào trong suốt lượt migrate — "
        "`run_migrations_online` chưa ôm khoá"
    )


def test_nha_khoa_sau_khi_xong(empty_db: str):
    assert _run_alembic(empty_db).returncode == 0
    assert _count_locks(empty_db) == 0, "khoá còn treo sau khi migrate xong"
