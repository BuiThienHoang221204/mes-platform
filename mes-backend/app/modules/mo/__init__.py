"""Lệnh sản xuất — vòng đời một MO TRƯỚC khi xuống xưởng. Vai PLANNER.

    models.py  schemas.py  repository.py  service.py  router.py
    bảng: manufacturing_order

Bảng gốc của cả hệ thống, nên 8/10 module còn lại đều import `mo`. Ranh giới của
module là mốc Submit: trước đó lệnh còn sửa, sau đó khoá cứng (§4A).
"""
