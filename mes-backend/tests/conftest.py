"""Dựng Postgres THẬT cho mỗi lần chạy test.

Hơn một nửa luật nghiệp vụ nằm trong CHECK / EXCLUDE USING gist / RULE / chỉ mục
duy nhất một phần. SQLite không có những thứ đó — test trên SQLite cho màu xanh
mà không kiểm được gì, tệ hơn là không test.

Không có Docker thì đặt MES_TEST_DATABASE_URL trỏ vào một Postgres rỗng.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# Test KHÔNG được phụ thuộc .env của máy cá nhân: đặt trước khi bất kỳ module nào
# của app được import, vì `settings` dựng ngay lúc import.
os.environ.setdefault("MES_ENV", "test")
os.environ.setdefault("MES_JWT_SECRET", "khoa-chi-dung-cho-test-" + "0" * 16)
os.environ.setdefault("MES_DATABASE_URL", "postgresql+psycopg://mes:mes@localhost:5432/mes")


@pytest.fixture(scope="session")
def db_url() -> Iterator[str]:
    url = os.getenv("MES_TEST_DATABASE_URL")
    if url:
        yield url
        return
    try:
        # Bản mới đổi chỗ; giữ cả hai để không kén phiên bản testcontainers.
        try:
            from testcontainers.community.postgres import PostgresContainer
        except ImportError:
            from testcontainers.postgres import PostgresContainer
    except ImportError:  # pragma: no cover
        pytest.skip("Chưa cài testcontainers — hoặc đặt MES_TEST_DATABASE_URL")

    # Cài testcontainers rồi nhưng Docker chưa chạy thì BỎ QUA, đừng báo lỗi:
    # lỗi ở đây là lỗi môi trường máy, không phải lỗi của code đang test.
    try:
        pg = PostgresContainer("postgres:16-alpine", driver="psycopg")
        pg.start()
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Không chạy được Docker ({type(e).__name__}) — "
                    f"bật Docker Desktop, hoặc đặt MES_TEST_DATABASE_URL")
    try:
        yield pg.get_connection_url()
    finally:
        pg.stop()


@pytest.fixture(scope="session")
def engine(db_url: str):
    os.environ["MES_DATABASE_URL"] = db_url
    from alembic import command
    from alembic.config import Config

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(cfg, "head")

    eng = create_engine(db_url, future=True)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    """Mỗi test một transaction rồi rollback — không test nào thấy rác của test khác."""
    conn = engine.connect()
    trans = conn.begin()
    session = sessionmaker(bind=conn, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()


# ── Dữ liệu mẫu ─────────────────────────────────────────────────────────────
@pytest.fixture
def actor(db: Session) -> uuid.UUID:
    """Tài khoản giữ ĐỦ 13 vai — để test luồng khỏi vướng phân quyền.

    Lấy từ `ROLES` chứ không gõ tay: thêm phòng ban thứ bảy thì fixture tự có,
    không âm thầm thiếu vai rồi hỏng một test chẳng liên quan gì tới quyền.
    """
    from app.common.security.permissions import ROLES
    from app.modules.auth.models import AppUser

    user = AppUser(full_name="Kiểm thử", emp_code=f"T{uuid.uuid4().hex[:6]}",
                   roles=list(ROLES))
    db.add(user)
    db.flush()
    return user.id


@pytest.fixture
def reasons(db: Session) -> dict[str, int]:
    """Danh mục lý do — migration 0002 đã nạp, lấy một cái mỗi nhóm."""
    rows = db.execute(
        text("SELECT DISTINCT ON (group_code) group_code, id"
             " FROM reason_code ORDER BY group_code, id")
    ).all()
    return {r.group_code: r.id for r in rows}


@pytest.fixture
def make_mo(db: Session, actor: uuid.UUID):
    """Tạo một MO đã Submit — tức đã có vòng 1 đang mở, nằm ở hàng đợi Kho."""
    from app.modules.mo import service as mo_service

    counter = {"n": 0}

    def _make(qty: int = 10_000, minutes: int = 180, box: int = 0) -> str:
        counter["n"] += 1
        code = f"M{900000 + counter['n']:06d}"
        item = mo_service.NewMo(code, "Vỏ nhựa F3", qty, minutes * 60, box)
        mo_service.create(db, [item], actor)
        mo_service.submit(db, code, actor)
        return code

    return _make


@pytest.fixture
def flow(db: Session, actor: uuid.UUID):
    """Đi qua các trạm bằng lời gọi service — ngắn gọn cho test luồng.

    Từ khi service tự tra MO và tự khoá vòng, fixture này chỉ còn chuyền mã đi —
    không còn `round_of()` nữa. Đó cũng là thước đo: chỗ nào trước kia phải tự
    khoá thì nay không ai bên ngoài service phải biết tới khoá.
    """
    from app.modules.packing import repository as packing_repo
    from app.modules.packing import service as packing_service
    from app.modules.production import service as production_service
    from app.modules.qc import service as qc_service
    from app.modules.round import service as round_service
    from app.modules.round import step_service
    from app.modules.warehouse_in import service as warehouse_in_service
    from app.modules.warehouse_out import service as warehouse_out_service

    class Flow:
        def round_of(self, code: str):
            """Vòng đang mở — test dùng để ĐỌC trạng thái, không phải để khoá."""
            return round_service.lock_round(db, code)[1]

        def accept(self, code: str, step_no: int):
            _, rnd = round_service.lock_round(db, code)
            return step_service.accept(db, rnd=rnd, step_no=step_no, actor_id=actor)

        def handover(self, code: str):
            return warehouse_out_service.handover(db, code=code, actor_id=actor)

        def qc(self, code: str, result: str, reason: str | None = None):
            from app.common.vocab.enums import QcVerdict

            return qc_service.qc_decide(
                db, code=code, result=QcVerdict(result),
                reason_code_id=None, reason_text=reason, actor_id=actor,
            )

        def run_line(self, code: str, line_code: str = "L01"):
            production_service.assign_line(db, code=code, line_code=line_code, actor_id=actor)
            production_service.line_start(db, code=code, line_code=line_code, actor_id=actor)

        def close_production(self, code: str, ok: int, ng: int = 0, short: int = 0,
                             ng_reason: str | None = None, short_reason: str | None = None):
            return production_service.close_production(
                db, code=code, qty_ok=ok, qty_ng=ng, qty_short=short,
                ng_reason_code_id=None, ng_reason_text=ng_reason,
                short_reason_code_id=None, short_reason_text=short_reason, actor_id=actor,
            )

        def hourly(self, code: str, slot: int, qty: int, people: int = 10,
                   target: int | None = None):
            from datetime import date as _date

            from app.modules.production import hourly_service

            return hourly_service.add_hourly(
                db, code=code, work_date=_date(2026, 9, 15), slot_hour=slot,
                headcount=people, target_qty=target if target is not None else qty,
                qty=qty, note=None, actor_id=actor,
            )

        def pack_hourly(self, code: str, slot: int, boxes: int):
            from datetime import date as _date

            from app.modules.packing import hourly_service as pack_hourly_service

            return pack_hourly_service.add_packing_hourly(
                db, code=code, work_date=_date(2026, 9, 15), slot_hour=slot,
                boxes=boxes, note=None, actor_id=actor,
            )

        def pack_start(self, code: str):
            return packing_service.packing_start(db, code=code, actor_id=actor)

        def pack(self, code: str, qty: int, note: str = "Đủ"):
            _, rnd = round_service.lock_round(db, code)
            if packing_repo.get_packing(db, rnd.id) is None:
                packing_service.packing_start(db, code=code, actor_id=actor)
            return packing_service.packing_finish(db, code=code, qty_packed=qty,
                                                  note_text=note, actor_id=actor)

        def warehouse_in(self, code: str):
            return warehouse_in_service.complete(
                db, code=code, qty_received=None, actor_id=actor
            )

        def progress(self, code: str):
            return round_service.progress(db, self.round_of(code).mo_id)

    return Flow()
