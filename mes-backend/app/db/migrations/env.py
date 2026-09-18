"""Alembic env — URL lấy từ MES_DATABASE_URL, không để trong alembic.ini.

Người gọi ĐẶT SẴN `sqlalchemy.url` thì tôn trọng, không ghi đè: `tests/conftest.py`
trỏ alembic vào Postgres tạm của testcontainers. Ghi đè bằng `settings` ở đây thì
test lại chạy migration lên CSDL thật của máy phát triển.

`--autogenerate` BỊ CHẶN ở file này — xem `_chan_autogenerate` bên dưới.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.common.config import settings

config = context.config

# Chỉ điền khi người gọi chưa đặt. `alembic.ini` để trống ô này, nên chạy bằng
# dòng lệnh thì rơi vào nhánh dưới và lấy từ .env.
if not config.get_main_option("sqlalchemy.url", None):
    config.set_main_option("sqlalchemy.url", settings.database.url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# CỐ Ý để None — dự án này KHÔNG so lược đồ bằng metadata.
#
# `target_metadata` chỉ phục vụ autogenerate và `alembic check`. Cả hai đều cho kết
# quả SAI ở đây, vì chỉ mục và ràng buộc nằm trong SQL thô của `0001_init.py` mà
# model không khai lại — xem `_chan_autogenerate` bên dưới.
#
# Đặt None thay vì trỏ vào một `Base` nào đó là có chủ ý: trỏ vào `common/base.py`
# thì metadata RỖNG và autogenerate đề nghị xoá cả 16 bảng — hỏng nặng hơn, mà lại
# trông như đang có cấu hình đúng.
target_metadata = None


def _chan_autogenerate() -> None:
    """Từ chối `alembic revision --autogenerate`. Ở dự án này nó SINH RA LỆNH SAI.

    Phần lớn chỉ mục và ràng buộc được tạo bằng SQL thô trong `0001_init.py`, mà
    model không khai lại. Autogenerate nhìn model, không thấy chúng, và kết luận là
    thừa. Đo thật ngày 2026-09-15: nó đề nghị xoá **18 thứ**, trong đó có

        mo_round_one_open      chặn một MO có hai vòng cùng mở
        seg_one_open           chặn một chuyền có hai đoạn cùng mở
        refresh_token_con_song chỉ mục tra token còn hiệu lực

    Ba cái đó là ràng buộc GIỮ DỮ LIỆU ĐÚNG, không phải tối ưu tốc độ. File sinh ra
    trông rất bình thường — 18 dòng `drop_index` lẫn giữa nhau, review lướt là cho qua.

    Nên migration ở đây VIẾT TAY, cả bốn cái hiện có đều vậy:

        ./run.sh mig-new "them cot abc"      tạo file rỗng, tự viết `op.execute(...)`
        ./run.sh mig                         chạy lên

    `alembic check` cũng bị chặn: nó dùng chung bộ máy so sánh nên sai y hệt.

    `upgrade`, `downgrade`, `revision` (không cờ) và `command.upgrade()` mà
    `tests/conftest.py` gọi thì KHÔNG đụng tới — đã kiểm cả bốn.
    """
    cmd_opts = getattr(config, "cmd_opts", None)
    if cmd_opts is None:
        return                                  # gọi bằng API (conftest) — không phải dòng lệnh

    lenh = getattr(cmd_opts, "cmd", (None,))[0]
    ten_lenh = getattr(lenh, "__name__", "")
    if not (getattr(cmd_opts, "autogenerate", False) or ten_lenh == "check"):
        return

    raise SystemExit(
        f"\n[alembic] `{ten_lenh}` so lược đồ bằng metadata — bị chặn ở dự án này.\n"
        "  Lý do: chỉ mục và ràng buộc nằm trong SQL thô của 0001_init.py, model\n"
        "  không khai lại. Đo thật: autogenerate đề nghị XOÁ 18 thứ, gồm cả\n"
        "  mo_round_one_open và seg_one_open — hai ràng buộc chống đua.\n"
        "  Dùng:  ./run.sh mig-new \"mo ta thay doi\"   rồi tự viết op.execute(...).\n"
        "  Chi tiết: app/db/migrations/env.py :: _chan_autogenerate\n"
    )


_chan_autogenerate()


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
