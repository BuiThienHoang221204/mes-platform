#!/usr/bin/env bash
# Thay cho `make` — Windows không có sẵn `make`, Git Bash cũng không kèm.
# Dùng:  ./run.sh dev  ·  ./run.sh test  ·  ./run.sh lint  ·  ./run.sh mig
#
# Mọi lệnh chạy bằng Python của .venv, KHÔNG dùng Python toàn máy.
set -e
cd "$(dirname "$0")"

PY=.venv/Scripts/python.exe
[ -x "$PY" ] || PY=.venv/bin/python            # Linux / macOS
UV="python -m uv"                              # uv.exe chưa vào PATH trên máy này

# Nạp .env để các lệnh psql dưới đây có POSTGRES_USER / POSTGRES_PASSWORD.
[ -f .env ] && set -a && . ./.env && set +a

case "${1:-help}" in
  setup)   $UV venv && $UV pip install --python "$PY" -e ".[dev]" ;;
  install) $UV pip install --python "$PY" -e ".[dev]" ;;
  lock)    $UV lock ;;

  db)      docker compose up -d mes-db ;;      # chỉ Postgres
  db-stop) docker compose down ;;
  up)      docker compose up --build ;;        # cả ba dịch vụ

  # Xem dữ liệu. `psql` chạy TRONG container nên không cần cài gì trên máy.
  psql)    docker compose exec -e PGPASSWORD="$POSTGRES_PASSWORD" mes-db              psql -U "${POSTGRES_USER:-mes}" -d "${POSTGRES_DB:-mes}" ;;
  sql)     docker compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" mes-db              psql -U "${POSTGRES_USER:-mes}" -d "${POSTGRES_DB:-mes}" -c "${2:?cần câu SQL}" ;;
  tables)  docker compose exec -T -e PGPASSWORD="$POSTGRES_PASSWORD" mes-db              psql -U "${POSTGRES_USER:-mes}" -d "${POSTGRES_DB:-mes}" -c "\dt+" ;;

  dev)     $PY -m uvicorn app.main:app --reload --port "${2:-8000}" ;;

  # Giải phóng cổng — xem stop-port.ps1 để biết vì sao phải cả một file.
  stop)    powershell -NoProfile -ExecutionPolicy Bypass -File ./stop-port.ps1 -Port "${2:-8000}" ;;

  test)    $PY -m pytest "${@:2}" ;;
  lint)    $PY -m ruff check app tests ;;
  fmt)     $PY -m ruff check app tests --fix ;;

  # Tai lieu trong docs/ tro vao ma nguon bang link kem so dong. Code dich chuyen
  # la so dong lech. `docs` do lai va SUA; `docs-check` chi kiem (dung cho CI).
  docs)       $PY tools/docs_link.py && $PY tools/docs_check.py ;;
  docs-check) $PY tools/docs_link.py --check && $PY tools/docs_check.py ;;

  # Dữ liệu mẫu cho máy phát triển — mã lệnh đều bắt đầu bằng M2, xem tools/seed_demo.py
  seed-demo) $PY tools/seed_demo.py "${@:2}" ;;

  mig)     $PY -m alembic upgrade head ;;
  mig-new) $PY -m alembic revision -m "${2:?cần tên: ./run.sh mig-new \"them cot abc\"}" ;;
  mig-down) $PY -m alembic downgrade -1 ;;

  clean)   find app tests -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
           rm -rf .pytest_cache .ruff_cache mes_backend.egg-info ;;

  *) grep -E "^  [a-z-]+\)" "$0" | sed 's/).*//; s/^/  .\/run.sh/' ;;
esac
