"""Màn hình điều hành — CHỈ ĐỌC. Không thao tác, không transaction.

    schemas.py  service.py  router.py
    KHÔNG sở hữu bảng nào — chỉ đọc view

Module duy nhất không có `models.py` và `repository.py`. Nó đọc 4 module khác
nhưng không ai đọc nó — đầu cuối của chiều phụ thuộc.
"""
