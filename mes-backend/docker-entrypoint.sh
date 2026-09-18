#!/bin/sh
# Migration chạy TRƯỚC, xong mới tới API — đúng thứ tự của job `migrate` trong
# docker-compose.yml.
#
# Ở đây gộp được vào một tiến trình vì container CHỈ chạy MỘT worker (xem CMD của
# Dockerfile và render.yaml). BE-PLAN §10 cấm nhiều worker cùng `alembic upgrade`
# lúc khởi động — chúng giành nhau bảng `alembic_version`.
#
# Muốn tăng worker hay tăng số bản sao thì phải bỏ dòng alembic khỏi đây và đưa
# migration ra một bước riêng chạy trước khi triển khai. Xem docs/TRIEN-KHAI-RENDER.md §6.
set -e

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

# Render cấp cổng qua $PORT và cổng đó đổi theo từng lần triển khai. Đóng cứng 8000
# thì bộ cân bằng tải gọi vào cổng không ai nghe, và service bị coi là chết.
PORT="${PORT:-8000}"
echo "[entrypoint] uvicorn 0.0.0.0:${PORT}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" --proxy-headers --forwarded-allow-ips='*'
