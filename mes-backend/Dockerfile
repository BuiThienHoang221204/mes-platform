FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./
COPY docker-entrypoint.sh ./
# `tools/` không cần cho lúc chạy, nhưng có nó thì mở Shell của máy chủ là nạp được
# dữ liệu mẫu (`seed_demo.py`) lúc dựng lần đầu — vài KB, đổi lại đỡ phải gõ SQL tay.
COPY tools ./tools

EXPOSE 8000

# Gọi qua `sh` chứ không phải `["./docker-entrypoint.sh"]`: kho này clone được trên
# Windows, nơi git không giữ bit thực thi — dạng kia sẽ báo "permission denied" ở
# máy dựng ảnh mà không nói vì sao.
CMD ["sh", "/srv/docker-entrypoint.sh"]
