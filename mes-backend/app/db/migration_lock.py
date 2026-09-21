"""Khoá tư vấn của Postgres cho migration.

Để riêng một file KHÔNG import gì: `migrations/env.py` chỉ chạy được bên trong một
lượt alembic (nó đọc `alembic.context`, thứ chưa tồn tại lúc import thường), nên test
không lấy hằng số từ đó được. Chép lại con số sang test thì hai bên trôi khỏi nhau mà
không ai báo.
"""

from __future__ import annotations

MIGRATION_LOCK_KEY = 0x6D65_7331
"""Hai tiến trình cùng migrate thì XẾP HÀNG, không giành.

Không có nó thì cả hai đọc `alembic_version` thấy cùng một mốc, cùng chạy một
migration, và cái thứ hai gãy giữa chừng — có thể để lại lược đồ chạy dở. Đó là lý do
BE-PLAN §10 phải cấm nhiều worker cùng migrate lúc khởi động.

Xếp hàng thì khỏi cấm: tiến trình thứ hai chờ, vào sau đọc lại `alembic_version` và
thấy không còn gì để làm. Nhờ vậy `docker-entrypoint.sh` giữ được `alembic upgrade`
ngay trong lệnh khởi động, kể cả khi chạy nhiều bản sao.

Khoá theo PHIÊN chứ không theo giao dịch: `context.run_migrations()` tự commit giữa
chừng, mà khoá phải giữ qua hết cả loạt.
"""
