"""Mất kết nối CSDL phải HIỆN RA trong log, không lẫn vào lỗi ràng buộc."""

from __future__ import annotations

import logging

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError

from app.common.vocab.error_codes import Err
from app.main import _is_connect_error, app


class FakeConnectFailure(Exception):
    sqlstate = None


class FakeServerError(Exception):
    sqlstate = "23505"


def _operational(orig: Exception) -> OperationalError:
    return OperationalError("SELECT 1", {}, orig)


def test_loi_mo_ket_noi_duoc_nhan_ra():
    assert _is_connect_error(_operational(FakeConnectFailure("connection refused")))


def test_loi_phia_server_khong_bi_coi_la_mat_ket_noi():
    assert not _is_connect_error(_operational(FakeServerError("duplicate key")))


def test_loi_rang_buoc_khong_bi_coi_la_mat_ket_noi():
    assert not _is_connect_error(IntegrityError("INSERT", {}, FakeServerError("dup")))


def test_readyz_tra_503_va_noi_ro_dang_nham_toi_dau(monkeypatch):
    monkeypatch.setattr("app.main.probe_db", lambda: "OperationalError: connection refused")

    with TestClient(app) as client:
        res = client.get("/readyz")

    assert res.status_code == 503
    body = res.json()
    assert body["db"] is False
    assert body["code"] == Err.DB_UNAVAILABLE
    assert "5432" in body["target"]


def test_readyz_ok_thi_khong_keu(monkeypatch):
    monkeypatch.setattr("app.main.probe_db", lambda: None)

    with TestClient(app) as client:
        res = client.get("/readyz")

    assert res.status_code == 200
    assert res.json()["db"] is True


def test_mat_ket_noi_ghi_mot_dong_ERROR(monkeypatch, caplog):
    monkeypatch.setattr("app.main.probe_db",
                        lambda: "OperationalError: password authentication failed")

    with caplog.at_level(logging.ERROR, logger="mes"), TestClient(app) as client:
        client.get("/readyz")

    ghi = [r for r in caplog.records if "KHÔNG KẾT NỐI ĐƯỢC CSDL" in r.getMessage()]
    assert ghi, "mất kết nối mà log im lặng thì không ai biết"
    assert "5432" in ghi[0].getMessage()


def test_log_viet_duoc_tieng_viet_ra_console_ascii(capsys):
    """Console Windows là cp1252 — dấu tiếng Việt từng làm handler nuốt cả bản ghi."""
    from app.common.logging import setup_logging

    setup_logging()
    logging.getLogger("mes.test").error("KHÔNG KẾT NỐI ĐƯỢC CSDL — cổng đã bị chiếm")

    ra = capsys.readouterr().out
    assert "KHÔNG KẾT NỐI ĐƯỢC CSDL" in ra


@pytest.mark.parametrize("path", ["/healthz"])
def test_healthz_van_song_khi_db_chet(path, monkeypatch):
    monkeypatch.setattr("app.main.probe_db", lambda: "OperationalError: down")

    with TestClient(app) as client:
        assert client.get(path).status_code == 200
