"""Đăng nhập và cấp token. Không thuộc trạm nào.

    models.py  schemas.py  repository.py  service.py  router.py
    bảng: app_user · refresh_token    (refresh_token là HẠ TẦNG, không thuộc 14 sổ)

Module DUY NHẤT không import và không bị import bởi module nào — hoàn toàn độc lập.
Luật nằm ở `service.py`: refresh dùng một lần, gửi lại lần hai là thu hồi cả chuỗi.
"""
