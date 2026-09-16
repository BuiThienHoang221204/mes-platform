"""Cấu hình, gom theo NHÓM — tương đương `registerAs('database', …)` của @nestjs/config.

    MES_DATABASE_*   →  settings.database.url          (≈ config.get('database.url'))
    MES_JWT_*        →  settings.jwt.secret
    MES_SCAN_*       →  settings.scan.dedupe_seconds
    MES_COOKIE_*     →  settings.cookie.secure
    MES_CORS_*       →  settings.cors.origins

File này KHÔNG chứa giá trị. Nguồn giá trị, theo thứ tự ưu tiên:

    biến môi trường thật   >   file .env ở gốc dự án   >   mặc định của tham số chỉnh

`database.url` và `jwt.secret` KHÔNG có mặc định: thiếu là app từ chối khởi động.
Cho chúng một mặc định thì quên `.env` sẽ không báo gì — app cứ chạy, nối nhầm CSDL,
hoặc ký token bằng khoá ai đọc repo cũng biết. Thà gãy ngay lúc khởi động.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# Neo vào GỐC DỰ ÁN, không phải thư mục đang đứng: alembic, pytest và uvicorn hay
# được gọi từ những chỗ khác nhau — để ".env" trần thì lúc thấy lúc không.
ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"

def _config(prefix: str) -> SettingsConfigDict:
    """Cấu hình chung cho mọi nhóm, chỉ khác tiền tố biến môi trường.

    Viết thành hàm chứ không phải một `dict` rồi `**` mở ra: `SettingsConfigDict`
    là `TypedDict`, mở gói vào nó thì trình kiểm kiểu không biết `env_prefix` đã
    được truyền hay chưa nên báo "trùng tham số". Hàm thì kiểu rõ cả hai đầu.
    """
    return SettingsConfigDict(
        env_prefix=prefix,
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


# ══ Nhóm database ═══════════════════════════════════════════════════════════
class DatabaseSettings(BaseSettings):
    model_config = _config("MES_DATABASE_")

    url: str = Field(description="postgresql+psycopg://user:pass@host:5432/db")  # BẮT BUỘC
    pool_size: int = Field(default=5, gt=0)
    max_overflow: int = Field(default=5, ge=0)
    echo: bool = Field(default=False, description="In mọi câu SQL — chỉ bật khi soi lỗi")


# ══ Nhóm jwt ════════════════════════════════════════════════════════════════
class JwtSettings(BaseSettings):
    model_config = _config("MES_JWT_")

    # BẮT BUỘC. Sinh khoá: python -c "import secrets; print(secrets.token_urlsafe(48))"
    secret: str = Field(min_length=32, description="Khoá ký token — tối thiểu 32 ký tự")

    # Access NGẮN vì nó đi kèm mọi request, dễ lọt vào log và proxy.
    access_ttl_minutes: int = Field(default=15, gt=0, description="Token dùng cho mọi request")
    # Refresh dài hơn — đổi lấy access mới mà không bắt đăng nhập lại.
    refresh_ttl_days: int = Field(default=7, gt=0)
    # Token gắn vào thiết bị đặt cố định ở trạm, không ai đăng nhập lại mỗi ngày.
    station_ttl_days: int = Field(default=365, gt=0)


# ══ Nhóm scan ═══════════════════════════════════════════════════════════════
class ScanSettings(BaseSettings):
    model_config = _config("MES_SCAN_")

    dedupe_seconds: float = Field(
        default=2.0, gt=0, description="Đầu đọc bắn hai lần trong ngần này giây = một lần (§1b.3)"
    )


# ══ Nhóm cookie ════════════════════════════════════════════════════════════
class CookieSettings(BaseSettings):
    """Token nằm trong cookie httpOnly — JavaScript của trang KHÔNG đọc được.

    Đổi lại, trình duyệt tự gửi cookie kèm mọi request, kể cả request do trang
    khác kích hoạt — tức là mở cửa cho CSRF. `samesite` là thứ chặn điều đó.
    """

    model_config = _config("MES_COOKIE_")

    # Mặc định BẬT. Máy phát triển chạy http thì đặt false trong .env.
    secure: bool = Field(default=True, description="Chỉ gửi cookie qua HTTPS")

    # lax  — FE và BE CÙNG site (qua reverse proxy). Chặn được CSRF.
    # none — FE khác origin. Buộc secure=true, VÀ mất lá chắn CSRF của trình duyệt:
    #        lúc đó phải thêm CSRF token, xem BE-PLAN §6.
    # `Literal` chứ không phải `str` + pattern: ba giá trị này là thứ Starlette
    # nhận vào `set_cookie`, nên khai đúng kiểu ấy thì trình kiểm kiểu bắt được
    # lỗi ngay lúc viết, và Pydantic vẫn chặn giá trị lạ y như cũ lúc chạy.
    samesite: Literal["lax", "strict", "none"] = "lax"

    domain: str | None = Field(default=None, description="Bỏ trống = đúng host đang phục vụ")


# ══ Nhóm CORS ═══════════════════════════════════════════════════════════════
class CorsSettings(BaseSettings):
    model_config = _config("MES_CORS_")

    # Cookie đi kèm request thì KHÔNG được dùng "*" — trình duyệt chặn thẳng.
    # Phải liệt kê đúng origin của FE.
    origins: list[str] = Field(default=["http://localhost:3000"])


# ══ Gốc ═════════════════════════════════════════════════════════════════════
class Settings(BaseSettings):
    model_config = _config("MES_")

    env: str = Field(default="dev", description="dev | staging | prod")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JwtSettings = Field(default_factory=JwtSettings)
    scan: ScanSettings = Field(default_factory=ScanSettings)
    cookie: CookieSettings = Field(default_factory=CookieSettings)
    cors: CorsSettings = Field(default_factory=CorsSettings)


# (tên thuộc tính, tiền tố biến môi trường, lớp) — thêm nhóm mới thì thêm một dòng.
GROUPS = (
    ("database", "MES_DATABASE_", DatabaseSettings),
    ("jwt", "MES_JWT_", JwtSettings),
    ("scan", "MES_SCAN_", ScanSettings),
    ("cookie", "MES_COOKIE_", CookieSettings),
    ("cors", "MES_CORS_", CorsSettings),
)


@lru_cache
def get_settings() -> Settings:
    """Dựng từng nhóm RIÊNG để gom đủ mọi thứ còn thiếu trong MỘT thông báo.

    Để pydantic tự dựng nhóm qua `default_factory` thì nhóm đầu tiên hỏng là dừng —
    người vận hành sửa xong biến này lại gặp báo lỗi biến kia, sửa mò từng vòng.
    """
    missing: list[str] = []
    invalid: list[str] = []
    built: dict[str, BaseSettings] = {}

    for ten, prefix, Lop in GROUPS:
        try:
            built[ten] = Lop()
        except ValidationError as e:
            for x in e.errors():
                var = prefix + str(x["loc"][0]).upper()
                if x["type"] == "missing":
                    missing.append(var)
                else:
                    invalid.append(f"{var}: {x['msg']}")

    if missing or invalid:
        lines = []
        if missing:
            lines.append("Thiếu cấu hình bắt buộc: " + ", ".join(missing))
        if invalid:
            lines.append("Cấu hình không hợp lệ: " + " · ".join(invalid))
        lines.append(f"Tạo file .env ở {ROOT}:  cp .env.example .env")
        raise RuntimeError("\n".join(lines)) from None

    # `model_validate` chứ không `Settings(**built)`: `built` là dict trộn nhiều
    # kiểu nhóm, mở gói vào `__init__` thì trình kiểm kiểu thấy mọi tham số đều là
    # `BaseSettings` — kể cả `env` vốn là `str`. `model_validate` nhận cả dict,
    # vẫn kiểm đầy đủ y hệt lúc chạy.
    return Settings.model_validate(built)


settings = get_settings()
