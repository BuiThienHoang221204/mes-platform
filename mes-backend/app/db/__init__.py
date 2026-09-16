"""Kết nối và tiến hoá lược đồ CSDL.

    session.py     engine · sessionmaker · dependency get_db
    migrations/    Alembic — DDL, trigger, view viết tay bằng SQL thô

Migration viết SQL thô chứ không dùng autogenerate: mọi luật quan trọng nằm trong
CHECK / EXCLUDE / RULE mà autogenerate không sinh ra được.
"""
