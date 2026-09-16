"""Ai là ai, được làm gì, và token đi đường nào.

    permissions.py   ★ bảng quyền RBAC · `permission_for` — nơi RA QUYẾT ĐỊNH (PDP)
    actor.py         `Actor.require_step` — nơi THI HÀNH (PEP)
    tokens.py        băm PIN · phát/đọc JWT · refresh token
    cookies.py       đặt và xoá cookie chứa token

Tách PDP khỏi PEP là cố ý: luật §9b nằm TRỌN trong `permissions.py`, `actor.py` chỉ
hỏi rồi ném lỗi. Muốn đổi quyền của một phòng ban thì sửa đúng một tệp.

`deps.py` ở thư mục cha ráp ba thứ này lại thành `ActorDep` / `StationDep`.
"""
