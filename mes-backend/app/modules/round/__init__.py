"""Vòng chạy và bước — ★ TRỤC CHUNG của cả hệ thống.

    models.py  schemas.py  repository.py  service.py  step_service.py
    bảng: mo_round · mo_step          (KHÔNG có router.py)

Không phải màn hình của ai: 8 module khác import nó, không ai `POST` thẳng vào.
Mọi thao tác trạm đều mở đầu bằng `repository.lock_open_round`.
"""
