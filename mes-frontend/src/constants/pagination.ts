/**
 * Cỡ trang của cả ứng dụng — khớp `PAGE_SIZE` trong `app/common/deps.py`.
 *
 * Khai một chỗ vì đây là con số người dùng nhìn thấy: mỗi màn một cỡ thì họ không
 * đoán được bấm `Xem thêm` sẽ ra bao nhiêu dòng, và test phải nhớ từng con số một.
 */
export const PAGE_SIZE = 10;
export const PAGE_MAX = 100;
