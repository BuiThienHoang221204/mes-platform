"""Trạm 0 — Kho bàn giao xuống xưởng. Vai KHO.

    models.py  repository.py  service.py  router.py
    bảng: warehouse_out                   (không có schemas.py — bàn giao không nhận body)

Chỉ còn MỘT thao tác là bàn giao; bước In phiếu đã bỏ từ BRD v2.18.
`round/step_service.py` đọc sổ này để chặn Setup nhận lệnh khi Kho chưa bàn giao.
"""
