"""Vốn từ — mọi giá trị hằng của hệ thống, tra ở đây.

    enums.py         MoStatus · QcVerdict · SegmentKind · ReasonGroup · STEP_NAMES
    error_codes.py   Err      — mã lỗi trả cho FE
    action_codes.py  Act      — `mo_event.action`
    state_names.py   State    — `mo_event.from_state` / `to_state`

Bốn tệp này KHÔNG import gì của dự án cả — đó là điều kiện để ở đây. Nhờ vậy tệp
nào cũng nhập được mà không sợ vòng lặp import.

Ba tệp cuối đều có bài kiểm cùng tên canh: không còn chuỗi trần, giá trị đúng bằng
tên, và khai ra thì phải có nơi dùng.
"""
