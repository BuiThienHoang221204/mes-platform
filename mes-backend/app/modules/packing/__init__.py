"""Đóng thùng — chạy SONG SONG với Sản xuất, không phải bước nối tiếp.

    models.py  schemas.py  repository.py  service.py  hourly_service.py  router.py
    bảng: packing · packing_hourly

Thuộc phòng **Sản xuất**, nằm TRONG trạm 4 (§7b, §9b.4) — không có vai riêng, mọi
endpoint kiểm bằng `require_step(4)`. Bàn team leader cũng đóng thùng được.

`hourly_service` tách riêng theo đúng khuôn của `production/`: ghi ĐỘC LẬP với chốt
sổ, người đếm thùng trong ca và người chốt `qty_packed` là hai người khác nhau.

Hai sổ, hai vai trò khác hẳn nhau:

    packing         sổ CHỐT của vòng — `qty_packed` (PCS) đẩy tiến độ MO (§6b.2)
    packing_hourly  nhật ký TRONG CA — đếm THÙNG ĐẦY, để thấy nhịp và số lẻ đang tồn

Tiến độ MO chỉ đọc `packing.qty_packed`, không bao giờ đọc `packing_hourly`. Hai sổ
độc lập để đối soát nhau — giống quan hệ `hourly_output` ↔ `production.qty_ok`.

Phụ thuộc `production` vì phải có chuyền đã chạy mới cho bắt đầu đóng thùng, và vì
số đã làm ra là trần của số đóng được.
"""
