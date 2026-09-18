"""Cache đọc — phải nhanh, nhưng không được trả số cũ sau khi có người ghi."""

from __future__ import annotations

from app.common import read_cache


def setup_function() -> None:
    read_cache.clear()


def test_goi_lai_trong_cung_khoang_thi_dung_lai_ket_qua():
    dem = {"n": 0}

    def produce():
        dem["n"] += 1
        return dem["n"]

    assert read_cache.cached("k", produce) == 1
    assert read_cache.cached("k", produce) == 1
    assert dem["n"] == 1, "chỉ chạy truy vấn một lần cho nhiều lượt hỏi"


def test_ghi_xong_thi_lan_doc_ke_tiep_phai_tuoi():
    dem = {"n": 0}

    def produce():
        dem["n"] += 1
        return dem["n"]

    read_cache.cached("k", produce)
    read_cache.bump()
    assert read_cache.cached("k", produce) == 2, "bump phải làm mục cũ vô hiệu ngay"


def test_khoa_theo_tung_key():
    read_cache.cached("a", lambda: "A")
    read_cache.cached("b", lambda: "B")
    assert read_cache.cached("a", lambda: "KHAC") == "A"
    assert read_cache.cached("b", lambda: "KHAC") == "B"


def test_ghi_xen_vao_giua_luc_doc_thi_khong_cache_so_cu():
    """Có người ghi trong lúc truy vấn đang chạy — kết quả đó đã cũ, không giữ lại."""

    def produce_cham():
        read_cache.bump()      # ai đó ghi xen vào giữa
        return "so-doc-duoc"

    read_cache.cached("k", produce_cham)

    dem = {"n": 0}

    def produce_sau():
        dem["n"] += 1
        return "so-moi"

    assert read_cache.cached("k", produce_sau) == "so-moi"
    assert dem["n"] == 1, "mục tạo lúc đang có người ghi phải tự hỏng"


def test_transactional_tu_bump(db, make_mo, flow):
    """Đi qua service thật: ghi xong là cache bảng phải thành cũ."""
    read_cache.clear()
    v0 = read_cache._version
    make_mo(qty=100, minutes=10)
    assert read_cache._version > v0, "@transactional phải gọi bump sau khi ghi"
