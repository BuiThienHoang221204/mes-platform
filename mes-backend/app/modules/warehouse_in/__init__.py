"""Trạm 5 — Nhập kho. Nơi MO đóng lại HOẶC chạy tiếp. Vai KHO.

    models.py  schemas.py  repository.py  service.py  router.py
    bảng: warehouse_in

Không module nào import `warehouse_in` — đây là cuối đường, chỉ nó gọi người khác.
Chỗ DUY NHẤT quyết định MO xong hay chưa, nên phải gọi `round`.
"""
