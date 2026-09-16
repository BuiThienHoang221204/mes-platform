"""Quét mã QR — MỘT cửa vào cho cả sáu trạm.

    models.py  schemas.py  repository.py  service.py  mocode.py  router.py
    bảng: scan_dedupe                 (HẠ TẦNG, không thuộc 14 sổ)

Trạm lấy từ token THIẾT BỊ chứ không từ body — mã QR chỉ nói MO nào (§1b.3).
`mocode.py` là bộ đọc mã thuần, không đụng DB; `mo` cũng dùng nó để kiểm mã.
"""
