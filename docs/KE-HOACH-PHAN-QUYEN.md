# Kế hoạch: phân quyền RBAC cho backend

> 2026-09-14 · Căn cứ `demo/BRD-v2-chot.md` v2.20 §9b · `mes-backend/BE-PLAN.md` v1.1 §6
> Mã nguồn: `mes-backend/`
> Hiện trạng: 30 endpoint · 16 bảng · **101 test xanh**
>
> ## ✅ ĐÃ TRIỂN KHAI — 2026-09-14
>
> Kế hoạch này đã thực hiện xong. Giữ lại vì phần **§1 vấn đề** và **§3 mô hình** là lý do đằng sau
> từng lựa chọn trong code — đọc `permissions.py` không thấy được.
>
> | Bước | Kết quả |
> |---|---|
> | PDP | `app/common/security/permissions.py` — bảng quyền + `permission_for()` |
> | PEP | `Actor.require_step()` trong `common/security/actor.py`, gọi ở 8 router |
> | Đổi vai | migration `0004_roles.py` + seed `0002` dùng 13 vai mới |
> | Test | `tests/test_permissions.py` — 42 ca, gồm một ca duyệt **mọi** endpoint |
>
> **Hai việc phải làm tay trước khi chạy thật** (migration in cảnh báo, không tự đoán được):
> gán `WAREHOUSE_IN_*` cho người ở **kho thành phẩm**, và nâng vài người lên `*_LEADER`.
>
> Nhân tiện phát hiện và sửa một lỗi **có sẵn từ trước, không liên quan phân quyền**:
> `current_actor` để hở một giao dịch chỉ-đọc nên `with db.begin()` ở router luôn ném
> *"A transaction is already begun"* — tức **mọi endpoint ghi trả 500 qua HTTP**. Test cũ không
> bắt được vì gọi thẳng service. Đã sửa trong `common/deps.py`, kèm `tests/test_deps.py`.

---

## 1. Vấn đề hiện tại

### 1.1 Bảy vai phẳng, không có khái niệm "phòng ban"

```python
ROLE_KHO  ROLE_SETUP  ROLE_QC  ROLE_BANCHO  ROLE_LEADER  ROLE_PACKING  ROLE_PLANNER
```

Bảy chuỗi rời nhau. Theo từ vựng RBAC: có **role**, có **user-role assignment** (`app_user.roles[]`),
nhưng **không có permission** và **không có role-permission assignment**. Nghĩa là chưa chỗ nào trong
code trả lời được *"vai này được làm gì trên step nào"*.

### 1.2 HAI KHO VẬT LÝ đang dùng CHUNG một vai

```python
STATION_ROLE = { 0: ROLE_KHO, …, 5: ROLE_KHO }   # ← cùng một vai
```

Đây không phải chuyện đặt tên. **Kho xuất (step 0) và Kho nhập (step 5) là hai kho khác nhau** — hai
toà nhà, hai tổ người:

| | Kho xuất · step 0 | Kho nhập · step 5 |
|---|---|---|
| Chứa | vật tư, bán thành phẩm | **thành phẩm** đã đóng thùng |
| Hàng đi | **ra**, xuống xưởng | **vào**, từ xưởng lên |
| Sổ | `warehouse_out` | `warehouse_in` |

Dùng chung một vai nghĩa là người giao vật tư **tự nhận luôn thành phẩm của chính lô mình giao** —
mất hẳn lớp đối soát giữa đầu vào và đầu ra của xưởng.

Trong RBAC, đây gọi là vi phạm **Separation of Duties** — xem §3.3. Là lỗ hổng **nghiệp vụ**, không
phải lỗi gõ nhầm.

### 1.3 Chỉ kiểm được "ai bấm", chưa kiểm được "ai xem"

Hiện chỉ có một câu hỏi duy nhất: *vai X có trong `roles` không*. Ba thứ BRD §9b đòi thì **chưa có
gì cả**:

| BRD §9b đòi | Code hiện có |
|---|---|
| Mỗi phòng chỉ thấy step của mình | ❌ không có khái niệm permission theo step |
| Mọi phòng đều **view** được step 4 | ❌ |
| Bàn team leader có **full** quyền step 4 | ❌ |

### 1.4 Mười endpoint không gọi `require_role`

Đo bằng máy — quét mọi `@router` trong `app/modules/*/router.py`:

| Nhóm | Endpoint | Đánh giá |
|---|---|---|
| auth | `/auth/login` · `/refresh` · `/logout` | **đúng** — ai cũng phải gọi được |
| catalog | `GET /lines` · `/reasons` | **chấp nhận được** — danh mục chỉ đọc |
| board | `/board/running` · `/queue/{station}` · `/counts` | **đúng với §9b.5** — bảng tổng quan |
| board | `GET /mos/{code}/trace` | ❌ **THIẾU** |
| mo | `GET /mos/{code}` | ❌ **THIẾU** |

Riêng `POST /scan` **không** nằm trong 10 cái trên: nó kiểm bằng `require_station`, tức là theo token
THIẾT BỊ thay vì theo vai người — đúng thiết kế (§1b.3).

`GET /mos/{code}/trace` là chỗ đáng lo nhất: nó trả **toàn bộ** lịch sử của một MO — mọi vòng, mọi
bước, ai làm gì lúc nào. Hiện **bất kỳ ai đăng nhập** đều xem được.

### 1.5 Leader và Member chưa tồn tại

Dữ liệu mẫu đang là `["KHO"]`, `["QC"]`… Không phân biệt cấp. Đổi sau khi xưởng đã phát tài khoản
thì phải sửa dữ liệu của mọi người dùng.

---

## 2. Yêu cầu — đọc lại cho chắc

Sáu phòng ban, mỗi phòng một step. Mỗi phòng hai cấp **Leader** và **Member**, **hiện quyền y hệt
nhau**. Hai mức quyền: **view** (xem) và **full** (xem + quét nhận + nhập sửa).

| Phòng ban | Step | Step của mình | Step 4 *(SX + Đóng thùng)* | Step khác |
|---|---|---|---|---|
| Kho xuất *(vật tư)* | 0 | Full | View | — |
| Setup | 1 | Full | View | — |
| QC | 2 | Full | View | — |
| **Bàn team leader** | 3 | Full | **FULL** | — |
| Sản xuất *(gồm Đóng thùng)* | 4 | Full | — | — |
| Kho nhập *(thành phẩm)* | 5 | Full | View | — |
| **PLANNER** | — | **Full mọi step** | Full | Full |

Ba điều dễ bỏ sót:

* **`Bảng đang chạy` là ngoại lệ** — mọi phòng ban đều xem được, vì nó là bảng tổng quan của cả xưởng
  (BRD §9b.5). Cái bị giới hạn là *màn hình thao tác của từng step*.
* **Đóng thùng không phải step riêng — nó nằm trong step 4.** Đóng thùng thuộc phòng Sản xuất, chạy song
  song với chuyền. Cột "Step 4" phủ **cả hai sổ** `production` và `packing`.
* **Vì vậy mức quyền trên step 4 áp cho cả đóng thùng**: Bàn team leader **full** step 4 thì đóng thùng được; các
  phòng khác **view** step 4 thì **cũng xem được số đóng thùng**.

13 vai = 6 phòng × 2 cấp + PLANNER.

---

## 3. Mô hình: RBAC

### 3.1 RBAC là gì, và ánh xạ sang dự án này

**RBAC** — *Role-Based Access Control*. Người không nhận quyền trực tiếp; người nhận **vai**, vai mới
mang **quyền**:

```
Người  ──UA──►  Vai  ──PA──►  Quyền  ──gác──►  Hành động
        (user-role   (permission-role
        assignment)   assignment)
```

Hai lớp gán đó là toàn bộ ý tưởng. Đổi việc của một người thì đổi vai; đổi luật của một phòng ban thì
đổi permission của vai — hai thao tác độc lập nhau.

| Thuật ngữ RBAC | Trong dự án | Nằm ở đâu |
|---|---|---|
| **Subject** (người) | `app_user` | bảng DB |
| **Role** (vai) | 13 vai: `QC_LEADER`, `WAITING_MEMBER`… | hằng trong code |
| **Resource** (đối tượng) | **step 0–5** | `mo_step.step_no` |
| **Permission** (quyền) | cặp *(step, mức)* — vd `(4, VIEW)` | — |
| **UA** — user-role | `app_user.roles[]` | bảng DB, đổi bằng SQL |
| **PA** — role-permission | bảng `ROLE_PERMISSIONS` | **code**, xem §3.4 |
| **PDP** — nơi ra quyết định | `permission_for(roles, step)` | `common/security/permissions.py` |
| **PEP** — nơi thi hành | `Actor.require_step(...)` ở router | 11 router |

Tách **PDP** (quyết định) khỏi **PEP** (thi hành) là điểm quan trọng nhất về mặt cấu trúc: luật nằm
đúng một chỗ, còn router chỉ hỏi. Muốn sau này chuyển luật xuống DB thì sửa ruột PDP, 30 endpoint
không đụng dòng nào.

### 3.2 Bốn bậc RBAC — dự án đang ở đâu

| Bậc | Là gì | Dự án |
|---|---|---|
| **RBAC0** | vai phẳng + gán quyền cho vai | ✅ **đợt này làm** |
| **RBAC1** | vai **kế thừa** nhau (Leader ⊃ Member) | ⏳ khi chốt Leader khác Member ở đâu |
| **RBAC2** | **ràng buộc**, nhất là Separation of Duties | ✅ **đợt này làm** — xem §3.3 |
| RBAC3 | cả 1 và 2 | — |

Leader/Member hiện quyền y hệt (BRD §9b.2), nên **chưa cần RBAC1**. Nhưng vai đã tách sẵn hai cấp, nên
ngày siết chỉ là cho `*_LEADER` kế thừa `*_MEMBER` rồi cộng thêm — không phải sửa dữ liệu tài khoản.

### 3.3 Separation of Duties — ràng buộc RBAC2

> Một người **không được** vừa giao vật tư xuống xưởng, vừa nhận thành phẩm của chính lô đó về kho.

Đây là SoD **tĩnh**: cấm ngay ở mức gán vai, không phải cấm lúc chạy. Hiện thực bằng cách tách hẳn hai
phòng ban `WAREHOUSE_OUT` và `WAREHOUSE_IN` — hai vai rời, không vai nào bao vai nào.

Hệ thống **không tự chặn** việc gán cả hai vai cho một người: xưởng nhỏ vẫn có thể cần vậy. Nhưng lúc
đó phải là **quyết định có chủ ý của người quản lý**, không phải hệ quả của việc hệ thống không phân
biệt nổi hai kho — đó chính là tình trạng hôm nay.

> Khi nào cần chặn cứng thì thêm một luật *mutually exclusive roles*: từ chối `UPDATE app_user` nếu
> `roles` chứa cả `WAREHOUSE_OUT_*` lẫn `WAREHOUSE_IN_*`. Chưa làm đợt này.

### 3.4 Đặt bảng PA ở đâu — ba cách

| | A · quyền rải theo endpoint | B · bảng PA trong code | C · `GRANT` của Postgres |
|---|---|---|---|
| Cách làm | `require_role("QC_LEADER")` từng endpoint | một `dict` vai → {step: mức} | mỗi vai một DB role |
| Có PA tường minh không? | **không** — quyền ẩn trong 30 chỗ | **có, một chỗ** | có |
| Thêm phòng ban mới | sửa mọi router liên quan | **thêm một dòng** | thêm role + grant |
| Sai sót | dễ — 13 vai × 30 endpoint gõ tay | khó — luật ở một chỗ | khó |
| Đổi quyền có phải deploy? | có | có | không |
| Công sức | thấp | vừa | **cao** |
| Rủi ro | **cao** — nhân bản luật khắp nơi | thấp | vừa — đổi cả cách kết nối DB |

### 3.5 Chọn B — bảng PA trong code

Yêu cầu §9b là một **ma trận** (vai × step × mức). Ma trận thì phải để thành **dữ liệu một chỗ**,
không rải thành câu lệnh khắp 11 router. Thêm phòng ban thứ bảy là **thêm một dòng**.

Phương án C mạnh hơn — DB tự chặn kể cả khi backend có lỗi — nhưng phải đổi cách kết nối (mỗi request
một DB role), làm hỏng connection pool, và **chưa cần tới mức đó** khi backend là đường vào duy nhất.

**Đặt PA trong code chứ không trong DB**, vì: sáu phòng ban cố định, ma trận đổi hoạ hoằn một năm một
lần; để trong code thì nó đi cùng phiên bản code, được `ruff` soi, được test trực tiếp. Chuyển xuống DB
khi khách muốn tự cấu hình quyền, hoặc nhiều xưởng mỗi nơi một luật.

### 3.6 Vì sao KHÔNG dùng thư viện RBAC

Toàn bộ luật là **31 dòng code**. Kéo `casbin` / `oso` vào để thay 31 dòng thì đổi lại:

* một **DSL matcher** phải học
* hai file policy nằm ngoài code — không được lint, không được type-check
* một phụ thuộc nữa phải nâng cấp, một lớp nữa phải mò khi phân quyền chạy sai
* test khó hơn: thay vì `assert permission_for(["QC_MEMBER"], 4) == VIEW`, phải dựng enforcer rồi nạp
  policy

Thư viện RBAC giải bài toán **policy phức tạp và hay đổi**. Đây là ma trận 6×6 cố định.

Khi nào cân nhắc lại:

| Dấu hiệu | Việc cần làm |
|---|---|
| Nhiều xưởng, mỗi nơi luật khác | chuyển PA xuống **bảng DB** — vẫn chưa cần thư viện |
| Khách tự sửa quyền trên màn hình | như trên + màn hình quản trị |
| Quyền tới từng dòng dữ liệu *("chỉ xem MO của chuyền mình")* | đây là **ABAC** — lúc đó mới cân nhắc `casbin` |

---

## 4. Thứ tự ưu tiên

Xếp theo **rủi ro nếu không làm**, không theo độ dễ:

| Ưu tiên | Việc | Vì sao trước |
|---|---|---|
| **P0** | Tách `KHO` → `WAREHOUSE_OUT` + `WAREHOUSE_IN` | Vi phạm SoD đang mở: người giao vật tư tự nhận thành phẩm |
| **P0** | Thêm PEP cho `GET /mos/{code}` và `/mos/{code}/trace` | Truy vết đang **mở cho mọi người** |
| **P1** | 13 vai + bảng PA + PDP `permission_for` | Phần chính — RBAC0 |
| **P1** | Bàn team leader full quyền step 4 | Nghiệp vụ đang chặn nhầm người đúng |
| **P2** | Migration đổi UA: vai cũ → vai mới | Chạy được sau, nhưng phải xong **trước khi phát tài khoản thật** |
| **P3** | Lọc dữ liệu `/board/queue/{station}` theo phòng ban | Nice-to-have; `/board/running` thì không lọc (§9b.5) |
| **Sau** | RBAC1 — Leader kế thừa Member | Khi chốt hai cấp khác nhau ở đâu |
| **Sau** | Mutually exclusive roles (SoD cứng) | Khi cần cấm hẳn một người giữ cả hai kho |
| **Sau** | `GRANT` theo bảng ở Postgres | Khi có đường vào DB ngoài backend |

**P0 làm trước vì đó là lỗ hổng đang mở**, không phải vì dễ.

---

## 5. File phải sửa

### 5.1 Thêm mới

| File | Nội dung |
|---|---|
| `app/common/security/permissions.py` | **PDP** — 6 phòng ban · `ROLE_PERMISSIONS` · `permission_for()` |
| `app/db/migrations/versions/0004_roles.py` | đổi **UA**: `roles` cũ sang 13 vai mới |
| `tests/test_permissions.py` | ma trận §9b — mỗi ô một test |

### 5.2 Sửa

| File | Sửa gì |
|---|---|
| `app/common/security/actor.py` | 7 hằng → 13 vai · `STATION_ROLE` → `STATION_DEPARTMENT` · `Actor.require_step` (**PEP**) |
| `app/common/deps.py` | không đổi (Actor đã mang `roles`) |
| `app/modules/warehouse_out/router.py` | `ROLE_KHO` → `require_step(0)` |
| `app/modules/qc/router.py` | `ROLE_QC` → `require_step(2)` |
| `app/modules/production/router.py` | `ROLE_LEADER` → `require_step(4)` — 5 endpoint |
| `app/modules/packing/router.py` | `ROLE_PACKING` → `require_step(4)` — đóng thùng thuộc SX |
| `app/modules/warehouse_in/router.py` | `ROLE_KHO` → `require_step(5)` ← **đổi hành vi**: kho vật tư mất quyền nhập kho |
| `app/modules/mo/router.py` | giữ `ROLE_PLANNER`; thêm PEP cho `GET /mos/{code}` |
| `app/modules/board/router.py` | `/trace` thêm PEP; `/running` giữ mở (§9b.5) |
| `app/db/migrations/versions/0002_seed.py` | 8 tài khoản mẫu dùng vai mới |
| `tests/conftest.py` | fixture `actor` dùng 13 vai |
| `tests/test_auth.py` | `roles=["LEADER"]` → `["PRODUCTION_LEADER"]` |
| `mes-backend/BE-PLAN.md` §6 | bỏ dòng "Chưa làm" |
| `demo/DB-GON.md` §2 | ghi chú vai đã vào code |

**16 file.** Không đụng `models/`, `repository/`, `service/` — PEP nằm ở tầng HTTP.

---

## 6. Cách triển khai

### Bước 1 — PDP: `app/common/security/permissions.py`

```python
"""Điểm ra quyết định phân quyền (PDP) — MỘT chỗ duy nhất giữ luật RBAC.

Router chỉ hỏi `permission_for(...)`, không tự suy luận. Ngày nào chuyển bảng PA
xuống CSDL thì sửa ruột hàm này, 30 endpoint không đụng dòng nào.

Mô hình: RBAC0 (vai → quyền) + RBAC2 (Separation of Duties, xem hai kho dưới đây).
"""

from __future__ import annotations

# ── Phòng ban = nhóm vai. HAI KHO khác nhau, không phải hai thao tác của một kho
#    (BRD §9b.1):
#      WAREHOUSE_OUT — kho vật tư, giao hàng XUỐNG xưởng      (step 0, sổ `warehouse_out`)
#      WAREHOUSE_IN  — kho thành phẩm, nhận hàng TỪ xưởng lên (step 5, sổ `warehouse_in`)
#    Tách rời là cách RBAC hiện thực Separation of Duties.
WAREHOUSE_OUT = "WAREHOUSE_OUT"
SETUP = "SETUP"
QC = "QC"
WAITING = "WAITING"
PRODUCTION = "PRODUCTION"
WAREHOUSE_IN = "WAREHOUSE_IN"

PLANNER = "PLANNER"          # vai đặc biệt: full mọi step, không thuộc phòng nào

LEADER, MEMBER = "LEADER", "MEMBER"   # hai cấp, hiện quyền Y HỆT (BRD §9b.2)

# Mức quyền trên một step
VIEW = "view"   # chỉ xem
FULL = "full"   # xem + quét nhận + nhập sửa

# Trạm nào thuộc phòng ban nào — dùng cho `require_station` khi quét QR.
STATION_DEPARTMENT: dict[int, str] = {
    0: WAREHOUSE_OUT, 1: SETUP, 2: QC, 3: WAITING, 4: PRODUCTION, 5: WAREHOUSE_IN,
}

# ══ Bảng PA — permission-role assignment. TOÀN BỘ luật nằm ở đây. ═══════════
ROLE_PERMISSIONS: dict[str, dict[int, str]] = {
    WAREHOUSE_OUT: {0: FULL, 4: VIEW},
    SETUP:         {1: FULL, 4: VIEW},
    QC:            {2: FULL, 4: VIEW},
    WAITING:       {3: FULL, 4: FULL},   # §9b.4 — ngoại lệ DUY NHẤT
    PRODUCTION:    {4: FULL},
    WAREHOUSE_IN:  {5: FULL, 4: VIEW},
}
# Không có khoá riêng cho Đóng thùng: đóng thùng nằm TRONG step 4 (BRD §7b, §9b.4).
# Nên {4: FULL} = ghi được cả `production` lẫn `packing`, và {4: VIEW} = xem được cả hai.

# 13 vai, SINH RA từ bảng PA — không gõ tay, không sót.
ROLES: list[str] = [f"{d}_{g}" for d in ROLE_PERMISSIONS for g in (LEADER, MEMBER)] + [PLANNER]


def department_of(role: str) -> str | None:
    """'QC_LEADER' → 'QC'. Vai lạ hoặc PLANNER → None."""
    return role.rsplit("_", 1)[0] if role.endswith(("_LEADER", "_MEMBER")) else None


def permission_for(roles: tuple[str, ...] | list[str], step_no: int) -> str | None:
    """PDP — mức quyền CAO NHẤT của người này trên một step. None = không thấy.

    Trả mức cao nhất vì một người giữ được nhiều vai: kiêm QC và Bàn team leader thì được
    FULL trên step 4 nhờ vai Bàn team leader, dù vai QC chỉ cho VIEW.
    """
    if PLANNER in roles:
        return FULL
    best = None
    for role in roles:
        level = ROLE_PERMISSIONS.get(department_of(role), {}).get(step_no)
        if level == FULL:
            return FULL
        if level == VIEW:
            best = VIEW
    return best
```

Ba quyết định:

* **`ROLES` sinh từ `ROLE_PERMISSIONS`** — thêm phòng ban thì danh sách vai tự dài ra, không sót.
* **`permission_for` trả mức CAO NHẤT** vì `roles` là mảng, một người giữ nhiều vai.
* **PLANNER thoát ngay đầu hàm**, không nhét vào bảng PA — nó không phải phòng ban, và nếu nhét vào thì
  phải liệt kê đủ 6 step, sót một cái là mất quyền mà không ai biết.

### Bước 2 — PEP: `Actor.require_step`

```python
def require_step(self, step_no: int, level: str = FULL) -> None:
    """PEP — thi hành quyết định của PDP tại router."""
    granted = permission_for(self.roles, step_no)
    if granted is None:
        raise Forbidden(f"{self.full_name} không thuộc phòng ban của {STEP_NAMES[step_no]}")
    if level == FULL and granted == VIEW:
        raise Forbidden(f"{self.full_name} chỉ được XEM {STEP_NAMES[step_no]}, không thao tác được")
```

**Hai câu lỗi khác nhau** — "không thuộc phòng ban" và "chỉ được xem" là hai tình huống khác hẳn; gộp
một câu thì người ở xưởng không biết nên đi hỏi ai.

`require_role` **giữ nguyên**, vẫn dùng cho PLANNER ở các endpoint của `mo/` — đó là kiểm theo vai,
không theo step.

### Bước 3 — gắn PEP vào router

```python
# warehouse_out/router.py    ← kho vật tư
- actor.require_role(ROLE_KHO)
+ actor.require_step(0)

# warehouse_in/router.py     ← ĐỔI HÀNH VI, không chỉ đổi tên
- actor.require_role(ROLE_KHO)       # kho vật tư cũng vào được
+ actor.require_step(5)              # chỉ kho thành phẩm

# packing/router.py          ← đóng thùng nằm TRONG step 4, không có step riêng
- actor.require_role(ROLE_PACKING)
+ actor.require_step(4)              # ghi: chỉ Sản xuất, Bàn team leader, PLANNER

# board/router.py            ← trace đang mở cho mọi người
+ actor.require_step(4, VIEW)   # ai xem được step 4 thì xem được truy vết
```

Riêng `/board/running` **không thêm PEP** — §9b.5 nói rõ mọi phòng ban đều xem được.

**Số đóng thùng không cần endpoint riêng để xem.** Nó đi kèm trong `GET /mos/{code}` và các màn hình
bảng, nên `require_step(4, VIEW)` ở hai chỗ đó là đã mở quyền xem đóng thùng cho mọi phòng ban. Hiện
**mọi vai đều thoả** `require_step(4, VIEW)` — đúng ý §9b.4, và câu kiểm này chỉ bắt đầu chặn khi có
vai mới không được xem step 4 (ví dụ vai cho khách hàng xem tiến độ).

### Bước 4 — migration `0004_roles.py`: đổi UA

```sql
UPDATE app_user SET roles = ARRAY['WAREHOUSE_OUT_MEMBER'] WHERE roles @> ARRAY['KHO'];
UPDATE app_user SET roles = ARRAY['SETUP_MEMBER']         WHERE roles @> ARRAY['SETUP'];
UPDATE app_user SET roles = ARRAY['QC_MEMBER']            WHERE roles @> ARRAY['QC'];
UPDATE app_user SET roles = ARRAY['WAITING_MEMBER']       WHERE roles @> ARRAY['BANCHO'];
UPDATE app_user SET roles = ARRAY['PRODUCTION_MEMBER']    WHERE roles @> ARRAY['LEADER','PACKING'];
```

**Không đoán được ai là Leader** — dữ liệu cũ không có thông tin đó, nên đổi hết thành `MEMBER`, rồi
nâng tay vài người. Đoán bừa rồi gán Leader là tệ hơn.

`KHO` cũ **không tự tách được** thành hai kho — dữ liệu không nói ai thuộc kho nào. Migration đổi hết
thành `WAREHOUSE_OUT_MEMBER` (kho vật tư) và **in cảnh báo**: người của **kho thành phẩm** phải gán tay
`WAREHOUSE_IN_*`.

> **Đây là bước bắt buộc làm tay trước khi chạy thật.** Để nguyên thì cả hai kho đều mang vai kho vật
> tư, và không ai nhập kho thành phẩm được — người ở trạm 5 bấm mãi không được mà không hiểu vì sao.

### Bước 5 — test

**Test PDP** — mỗi ô của ma trận §9b một ca:

```python
@pytest.mark.parametrize("role,step,expected", [
    ("QC_MEMBER",            2, FULL), ("QC_MEMBER",         4, VIEW),
    ("QC_MEMBER",            0, None), ("WAITING_MEMBER",    4, FULL),   # ngoại lệ
    ("WAREHOUSE_OUT_MEMBER", 5, None),   # SoD: kho vật tư KHÔNG nhập kho thành phẩm
    ("WAREHOUSE_IN_MEMBER",  0, None),   # SoD: và ngược lại
    ("WAREHOUSE_IN_MEMBER",  4, VIEW),   # xem được đóng thùng — nằm trong step 4
    ("SETUP_MEMBER",         4, VIEW),   # nt
    ("PLANNER",              0, FULL), ("PLANNER",           5, FULL),
])
def test_ma_tran_quyen(role, step, expected):
    assert permission_for([role], step) is expected


def test_giu_nhieu_vai_thi_lay_muc_CAO_NHAT():
    """Kiêm QC (view step 4) và Bàn team leader (full step 4) → được FULL."""
    assert permission_for(["QC_MEMBER", "WAITING_MEMBER"], 4) == FULL
```

**Test PEP** — bốn ca qua HTTP thật:

| Ai gọi | Gọi gì | Phải ra |
|---|---|---|
| `QC_MEMBER` | `POST /v1/warehouse-out/{code}/handover` | **403** — không thuộc phòng Kho vật tư |
| `QC_MEMBER` | `GET /v1/board/running` | **200** — bảng tổng quan, ai cũng xem (§9b.5) |
| `WAITING_MEMBER` | `POST /v1/production/{code}/close` | **200** — ngoại lệ Bàn team leader |
| `WAITING_MEMBER` | `POST /v1/packing/{code}/finish` | **200** — full step 4 gồm cả đóng thùng |
| `QC_MEMBER` | `POST /v1/packing/{code}/finish` | **403** — chỉ view step 4, không ghi |
| `QC_MEMBER` | `GET /v1/mos/{code}` *(có số đóng thùng)* | **200** — view step 4 gồm xem đóng thùng |
| `WAREHOUSE_OUT_MEMBER` | `POST /v1/warehouse-in/{code}/complete` | **403** — SoD |

Dòng cuối là dòng đáng giá nhất: nó chứng minh vi phạm SoD ở §1.2 đã bịt.

**Test bảo vệ chính bảng PA:**

```python
def test_moi_step_deu_co_it_nhat_mot_phong_ban_FULL():
    for step in range(6):
        assert any(p.get(step) == FULL for p in ROLE_PERMISSIONS.values()), \
            f"step {step} không phòng ban nào thao tác được"


def test_moi_vai_deu_co_it_nhat_mot_quyen():
    for role in ROLES:
        assert any(permission_for([role], s) for s in range(6)), f"{role} không làm được gì"
```

Hai test này bắt lỗi sửa bảng PA làm mồ côi một step hoặc một vai — kiểu lỗi không endpoint nào báo,
chỉ lộ ra khi có người đứng ở trạm bấm mãi không được.

### Bước 6 — tài liệu

`mes-backend/BE-PLAN.md` §6 bỏ dòng "**Chưa làm:**". `demo/DB-GON.md` §2 ghi vai đã vào code.

---

## 7. Thứ tự chạy và cách kiểm

| # | Việc | Xong khi |
|---|---|---|
| 1 | PDP `permissions.py` + test ma trận | test ma trận xanh, **chưa đụng router** |
| 2 | PEP `Actor.require_step` | test cũ vẫn 59 xanh |
| 3 | Gắn PEP vào 6 router | test HTTP 403/200 xanh |
| 4 | Migration `0004` đổi UA + seed | `./run.sh mig` rồi `NV030` đăng nhập vẫn quét QC được |
| 5 | Tài liệu | — |

Mỗi bước chạy `./run.sh test && ./run.sh lint` trước khi sang bước sau. **Bước 1 và 2 không đổi hành
vi gì** — chỗ an toàn để dừng lại nếu hết thời gian.

---

## 8. Rủi ro

| Rủi ro | Chặn bằng cách |
|---|---|
| Đổi `warehouse_in` sang `require_step(5)` khoá mất người đang nhập kho | **Chắc chắn xảy ra** — mọi tài khoản `KHO` cũ thành kho vật tư. Migration in cảnh báo; phải gán tay `WAREHOUSE_IN_*` trước khi deploy |
| Sót một endpoint, nó thành mở toang | Test liệt kê **mọi** endpoint và khẳng định từng cái đòi quyền gì |
| Bảng PA sửa sai làm mồ côi một step hoặc một vai | Hai test ở bước 5 |
| Leader/Member gán nhầm | Hiện quyền y hệt nhau nên **chưa gây hại** — sửa được trước khi siết |
| Một người vô tình giữ cả hai vai kho | Hệ thống KHÔNG chặn (§3.3). Rà `roles` bằng SQL trước khi chạy thật |

---

## 9. Không làm trong đợt này

* **RBAC1 — Leader kế thừa Member.** BRD §9b.2 nói rõ hai cấp hiện quyền y hệt. Đợi xưởng chạy thật.
* **SoD cứng — mutually exclusive roles.** Chặn gán cả hai vai kho cho một người. Chưa cần: xưởng nhỏ
  đôi khi phải kiêm thật.
* **`GRANT` theo bảng ở Postgres.** Chỉ đáng khi có đường vào DB ngoài backend.
* **Chuyển bảng PA xuống CSDL.** Khi khách muốn tự cấu hình quyền, hoặc nhiều xưởng mỗi nơi một luật.
* **Thư viện RBAC** (`casbin`, `oso`). Xem §3.6 — chưa đáng ở quy mô ma trận 6×6.
* **Lọc dữ liệu `/board/running` theo phòng ban.** BRD §9b.5 nói rõ không lọc.
* **Màn hình quản trị gán vai.** Dùng SQL tay cho tới khi có yêu cầu thật.
