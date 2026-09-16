"""Ranh giới giao dịch — một đơn vị công việc (unit of work).

Tương đương `@Transactional()` của NestJS/Spring với propagation **REQUIRED**:
hàm nào gắn `@transactional` mà được gọi từ trong một giao dịch đang chạy thì
**nhập vào** giao dịch đó, không mở cái mới. Nhờ vậy service gọi service được —
`warehouse_in.complete` gọi `round_service.open_next_round` vẫn là MỘT
đơn vị công việc.

Vì sao cần ở đây mà không để router tự mở: khoá dòng (`SELECT … FOR UPDATE` trong
`round_service.lock_round`) chỉ sống bên trong một giao dịch và nhả lúc commit.
Khoá và phần ghi phải nằm chung một giao dịch, mà chỉ service mới biết cặp đó
gồm những gì.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from typing import Any, TypeVar

from sqlalchemy.orm import Session

# Đánh dấu "giao dịch này DO MÌNH mở". Dùng ContextVar chứ không phải thuộc tính
# của Session vì nó tự cô lập theo từng request/luồng.
_owned: ContextVar[bool] = ContextVar("uow_owned", default=False)

T = TypeVar("T")


@contextmanager
def transaction(db: Session) -> Iterator[None]:
    """Mở một đơn vị công việc, hoặc nhập vào cái đang chạy.

    Ba tình huống:

    1. Lồng trong một `transaction()` khác → nhập vào, **không** commit ở đây.
    2. Session đang sạch → mở giao dịch mới, thoát êm thì commit, ném lỗi thì rollback.
    3. Session đã có giao dịch mà không phải của mình → mở một **SAVEPOINT**. Đơn
       vị công việc vẫn nguyên khối (hỏng thì nhả về mốc), còn commit hay rollback
       cái ngoài thì để người mở nó quyết định. Đây là đường fixture test đi: mỗi
       test bọc sẵn một giao dịch rồi rollback, nên test không để lại rác — mà
       hành vi "hỏng giữa chừng thì huỷ sạch" vẫn giống hệt lúc chạy thật.

    Tình huống 3 cũng là cái bẫy nếu gặp ở môi trường thật: ai đó lỡ chạy một câu
    SELECT trước khi gọi service thì SQLAlchemy tự mở giao dịch, hàm này tưởng là
    của người khác, và **không có ai commit**. Vì vậy `deps.current_actor` đóng lại
    giao dịch chỉ-đọc của nó ngay sau khi đọc, và router không được chạm CSDL.
    `tests/test_uow.py` canh đúng điều này bằng một session sạch.
    """
    if _owned.get():
        yield
        return

    token = _owned.set(True)
    try:
        with (db.begin_nested() if db.in_transaction() else db.begin()):
            yield
    finally:
        _owned.reset(token)


def transactional(fn: Callable[..., T]) -> Callable[..., T]:
    """Gắn lên hàm service là điểm vào của một thao tác nghiệp vụ.

    Tham số ĐẦU TIÊN phải là `Session` — quy ước của mọi service trong source này.
    """

    @wraps(fn)
    def wrapper(db: Session, *args: Any, **kwargs: Any) -> T:
        with transaction(db):
            return fn(db, *args, **kwargs)

    return wrapper
