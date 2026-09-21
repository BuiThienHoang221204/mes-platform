#!/bin/sh
# Migration chạy TRƯỚC, xong mới tới API — đúng thứ tự của job `migrate` trong
# docker-compose.yml.
#
# Gộp được vào một tiến trình vì `migrations/env.py` ôm khoá tư vấn của Postgres
# quanh cả loạt migration: hai tiến trình cùng chạy thì XẾP HÀNG chứ không giành
# `alembic_version`. Không cần tách migration ra bước deploy riêng nữa.
#
# Nhưng CHẠY thì vẫn phải một tiến trình — xem khối kiểm ngay dưới.
set -e

# Nhiều worker làm SSE và cache sai mà không báo gì (docs/RA-SOAT-POLLING.md §2/A1,
# §2/A2). `app/common/single_process.py` cũng chặn, nhưng chặn ở đây thì thông báo
# nằm ngay đầu log triển khai, không lẫn vào traceback của lifespan.
for bien in WEB_CONCURRENCY UVICORN_WORKERS GUNICORN_WORKERS; do
  eval "gia_tri=\${$bien:-}"
  [ -n "$gia_tri" ] || continue
  [ "$gia_tri" -gt 1 ] 2>/dev/null || continue
  if [ "${MES_ALLOW_MULTI_PROCESS:-false}" != "true" ]; then
    echo "[entrypoint] $bien=$gia_tri — ban nay chi chay MOT tien trinh." >&2
    echo "[entrypoint] Xem docs/RA-SOAT-POLLING.md muc 5.4 truoc khi tang." >&2
    exit 1
  fi
done

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

# Render cấp cổng qua $PORT và cổng đó đổi theo từng lần triển khai. Đóng cứng 8000
# thì bộ cân bằng tải gọi vào cổng không ai nghe, và service bị coi là chết.
PORT="${PORT:-8000}"
echo "[entrypoint] uvicorn 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips='*'
