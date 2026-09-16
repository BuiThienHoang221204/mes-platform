"""Sổ `mo_event` — CHỈ GHI THÊM, không sửa không xoá.

    models.py        bảng `mo_event`
    repository.py    `log` · `events_of`

RULE dưới CSDL chặn UPDATE và DELETE, nên một dòng ghi sai nằm lại vĩnh viễn. Đó là
lý do `log()` nhận `Act` chứ không nhận `str`, và vì sao `vocab/action_codes.py` với
`vocab/state_names.py` có bài kiểm canh riêng.

9/10 service đều gọi `log` — đây là thứ dùng chung nhất của cả hệ thống.
"""
