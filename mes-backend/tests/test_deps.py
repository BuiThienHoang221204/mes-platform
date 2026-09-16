"""Ranh giới giao dịch của một request.

Test ở đây KHÔNG dùng fixture `db` chung: fixture đó bọc sẵn mỗi test trong một
transaction rồi rollback, nên nó che mất đúng cái lỗi cần bắt. Phải dựng session
sạch như lúc chạy thật.
"""

from __future__ import annotations

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from app.common.deps import current_actor
from app.common.security.tokens import make_access_token
from app.modules.auth.models import AppUser

EMP = "T-DEPS-01"


@pytest.fixture
def phien_sach(engine):
    """Session độc lập, giống hệt `SessionLocal` của app lúc chạy thật."""
    tao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    s = tao()
    try:
        yield s
    finally:
        s.rollback()
        s.execute(delete(AppUser).where(AppUser.emp_code == EMP))
        s.commit()
        s.close()


def test_doc_actor_xong_ROUTER_VAN_MO_DUOC_GIAO_DICH(phien_sach):
    """`current_actor` chạy một SELECT, mà SELECT thì SQLAlchemy TỰ mở giao dịch.

    Không đóng lại thì `with db.begin()` ở router ném "A transaction is already
    begun on this Session" — nghĩa là MỌI endpoint ghi trả 500. Lỗi này từng sống
    được lâu vì test cũ gọi thẳng service, không đi qua tầng dependency.
    """
    user = AppUser(full_name="Hồi quy", emp_code=EMP, roles=["QC_MEMBER"])
    phien_sach.add(user)
    phien_sach.commit()

    actor = current_actor(phien_sach, cookie_token=make_access_token(user.id))
    assert actor.roles == ("QC_MEMBER",)
    assert actor.full_name == "Hồi quy"

    # Dòng này chính là dòng từng nổ. Không assert gì — nó ném là test đỏ.
    with phien_sach.begin():
        pass
