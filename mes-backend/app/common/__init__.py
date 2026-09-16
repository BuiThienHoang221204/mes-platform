"""Hạ tầng mọi module đều dùng. KHÔNG phải một tính năng.

Ba nhóm có thư mục riêng — mở `__init__.py` của từng nhóm để biết trong đó có gì:

    vocab/       vốn từ: `MoStatus` · `Err` · `Act` · `State` · `STEP_NAMES`
    security/    ai là ai, được làm gì, token đi đường nào
    event_log/   sổ `mo_event` — chỉ ghi thêm

Còn lại để phẳng, vì mỗi tệp là một việc rời, không tệp nào hợp thành nhóm với
tệp nào:

    base.py      `Base` — lớp cha mọi bảng ORM
    uow.py       ★ `transaction` · `@transactional` — ranh giới giao dịch
    deps.py      `DbDep` · `ActorDep` · `StationDep` — ráp cho router
    errors.py    4 lớp lỗi · `CONSTRAINT_MESSAGES` · `translate_db_error`
    schemas.py   `MoCode` · `StationNo` · `ErrorOut` · `OkOut`
    config.py    đọc `.env` thành `settings`
    clock.py     `now` · `db_now` · `db_clock` — giờ lấy TỪ CSDL
    logging.py   log JSON kèm mã request

Hai chỗ đánh ★ giữ một luật cho CẢ hệ thống — `uow.py` mở giao dịch,
`security/permissions.py` trả lời quyền. Sửa chúng là đổi hành vi mọi module
cùng lúc.

Sửa bất cứ tệp nào ở đây là MỌI module chịu ảnh hưởng — khác hẳn sửa trong
`modules/`, nơi tác động dừng lại trong một thư mục.
"""
