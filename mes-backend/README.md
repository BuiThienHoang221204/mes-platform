# MES Backend

Python + PostgreSQL. Thiết kế theo `../BE-PLAN.md`, lược đồ theo `../DB-GON.md`,
nghiệp vụ theo `../BRD-v2-chot.md`.

## Chạy

Lần đầu:

```bash
cp .env.example .env      # rồi sửa MES_JWT_SECRET và POSTGRES_PASSWORD
./run.sh setup            # tạo .venv + cài phụ thuộc
./run.sh db               # Postgres trong Docker
./run.sh mig              # tạo bảng + nạp dữ liệu mẫu
./run.sh dev              # http://localhost:8000/docs
```

Những lần sau chỉ cần `./run.sh db && ./run.sh dev`.

Tám tài khoản mẫu, PIN đều `1234`: `NV001` PLANNER · `NV010` KHO · `NV030` QC ·
`NV050` LEADER · `NV060` PACKING. **Đổi PIN trước khi chạy thật.**

Chạy hết bằng Docker, giống máy thật hơn nhưng không tự nạp lại khi sửa code:

```bash
./run.sh up               # mes-db → migrate → api
```

`./run.sh` không tham số để xem đủ 15 lệnh. Windows không có `make`, nên dùng
script này thay `Makefile`; nó chạy được cả trên Linux/macOS.

## Kiểm thử

```bash
./run.sh test                             # 59 test, cần Docker cho testcontainers
./run.sh test tests/test_mocode.py        # một file
./run.sh lint                             # ruff
```

**Test chạy trên Postgres THẬT, không phải SQLite.** Hơn nửa luật nghiệp vụ nằm
trong `CHECK` / `EXCLUDE USING gist` / `RULE` / chỉ mục duy nhất một phần —
SQLite không có những thứ đó, test trên nó cho màu xanh mà không kiểm được gì.

## Đăng nhập để thử

Migration `0002` nạp sẵn 8 tài khoản mẫu, **PIN đều là `1234`** — đổi trước khi chạy thật.

```bash
# 1. lấy token người
curl -s localhost:8000/v1/auth/login -H 'content-type: application/json' \
     -d '{"emp_code":"NV010","pin":"1234"}'

# 2. Planner cấp token cho THIẾT BỊ đặt ở trạm (ví dụ trạm QC = 2)
curl -s -X POST 'localhost:8000/v1/auth/station-token?station=2' -H "authorization: Bearer $TOKEN"

# 3. quét: mã đi trong body, TRẠM đi trong header của thiết bị
curl -s localhost:8000/v1/scan -H "authorization: Bearer $TOKEN" \
     -H "x-station-token: $STATION_TOKEN" -H 'content-type: application/json' \
     -d '{"raw":"XM068820"}'
```

| Mã NV | Vai |
|---|---|
| NV001 | PLANNER |
| NV010 · NV070 | KHO |
| NV020 | SETUP |
| NV030 | QC |
| NV040 | BANCHO |
| NV050 | LEADER |
| NV060 | PACKING |

## Bố cục

```
app/
  core/         cấu hình · log · bảo mật · ÁNH XẠ LỖI DB → câu tiếng Việt
  db/           engine, session, migrations (DDL nguyên văn từ DB-GON.md)
  domain/       enum + 14 bảng (+1 bảng hạ tầng chống bắn trùng khi quét)
  schemas/      hợp đồng với FE, nhóm theo màn hình
  repositories/ câu truy vấn, khoá dòng
  services/     luật nghiệp vụ + ranh giới giao dịch
  api/          router — không chứa luật nghiệp vụ
```

Chiều phụ thuộc một chiều: `api → services → repositories → domain`.

## Ba điều quyết định mọi thứ còn lại

**① CSDL giữ luật, không phải Python.** `đạt + hỏng + thiếu = mục tiêu vòng`,
`một chuyền không chạy hai MO cùng lúc`, `nhật ký không sửa` — đã là `CHECK`,
`EXCLUDE`, `RULE`. Service **không kiểm lại rồi mới ghi**; nó ghi, và
`core/errors.py` dịch lỗi thành câu người vận hành đọc được.

**② Số dẫn xuất đọc từ view.** `v_step_total`, `v_line_time`, `v_round_kpi`,
`v_mo_progress`, `v_hourly_reconcile`, `v_round_board`. Không tính lại bằng Python.

**③ Mốc giờ do server sinh.** `DEFAULT now()`, không nhận timestamp từ client.

## Ranh giới giao dịch

Mỗi thao tác của người vận hành = **một** `with db.begin()` ở router, bọc **một**
lời gọi service. Mọi service sửa vòng đều bắt đầu bằng `repo.lock_open_round()`
(`SELECT … FOR UPDATE`) — đó là chốt chống hai người quét cùng lúc.

## Còn treo

| # | Câu hỏi | Chặn phần nào |
|---|---|---|
| #36 | Mã MO do hệ thống cấp hay ERP? | `POST /v1/mos/batch` — nếu ERP cấp thì bỏ hẳn |
| #26 | Phân quyền siết tới đâu? | hiện kiểm ở service; chốt xong thì thêm `GRANT` theo bảng trạm |
| #40 | Bỏ in ở Kho thì QR từ đâu? | không chặn code, **chặn chạy thật** — không tem thì 6 trạm không quét được |
| #38 | Đóng thùng có cần ô nhập SL? | bỏ được thì `qty_packed` thành cột tính từ `production.qty_ok` |
