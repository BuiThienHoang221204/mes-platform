"""Trạm 4 — Sản xuất: chuyền, chốt sổ, sản lượng giờ. Vai LEADER.

    models.py  schemas.py  repository.py  service.py  hourly_service.py  router.py
    bảng: production · line_segment · hourly_output

Module nhiều bảng nhất. `hourly_service` tách riêng vì ghi ĐỘC LẬP với chốt sổ —
người nhập giờ và người chốt sổ là hai người khác nhau.
"""
