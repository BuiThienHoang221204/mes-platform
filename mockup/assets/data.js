/* ═══════════════════════════════════════════════════════════════
   data.js — Vai, ma trận quyền (§9b) và dữ liệu mẫu
   Số liệu cố định, chọn sao cho mỗi màn hình đều có đúng trạng
   thái cần minh hoạ: hàng đợi, đang chạy, rework, vòng 2, đã xong.
   ═══════════════════════════════════════════════════════════════ */
window.MES = (function () {
  "use strict";

  /* §9b.1 — Sáu phòng ban, mỗi phòng một step.
     Kho XUẤT (0) và Kho NHẬP (5) là hai kho vật lý khác nhau. */
  const DEPTS = [
    { id: 'wh_out', step: 0, nm: 'Kho xuất', full: 'Kho xuất · vật tư', desc: 'Bàn giao vật tư xuống xưởng', ic: '📦', at: 'Kho vật tư / bán thành phẩm' },
    { id: 'setup', step: 1, nm: 'Setup', full: 'Setup máy', desc: 'Chỉnh máy, gá khuôn trước khi chạy', ic: '🔧', at: 'Xưởng' },
    { id: 'qc', step: 2, nm: 'QC', full: 'QC · Kiểm tra', desc: 'Kiểm hàng sau setup — PASS hoặc FAIL', ic: '🔍', at: 'Xưởng' },
    { id: 'waiting', step: 3, nm: 'Bàn team leader', full: 'Bàn team leader', desc: 'Chờ vào chuyền — và điều phối Step 4', ic: '📋', at: 'Xưởng' },
    { id: 'prod', step: 4, nm: 'Sản xuất', full: 'Sản xuất · 14 line', desc: 'Chạy chuyền, chốt sổ và đóng thùng', ic: '⚙️', at: 'Xưởng' },
    { id: 'wh_in', step: 5, nm: 'Kho nhập', full: 'Kho nhập · thành phẩm', desc: 'Nhận thành phẩm về kho, chốt đơn', ic: '🏬', at: 'Kho thành phẩm' },
    { id: 'planner', step: null, nm: 'Planner', full: 'PLANNER · Điều độ', desc: 'Toàn quyền mọi step — vai điều độ', ic: '🗂️', at: 'Văn phòng điều độ' }
  ];

  /* §9b.7 — 6 phòng × 2 cấp + PLANNER = 13 vai */
  const ROLES = [
    { id: 'WAREHOUSE_OUT_LEADER', dept: 'wh_out', lv: 'Leader', who: 'Trần Văn Kho' },
    { id: 'WAREHOUSE_OUT_MEMBER', dept: 'wh_out', lv: 'Member', who: 'Lê Thị Vân' },
    { id: 'SETUP_LEADER', dept: 'setup', lv: 'Leader', who: 'Phạm Hữu Sơn' },
    { id: 'SETUP_MEMBER', dept: 'setup', lv: 'Member', who: 'Đỗ Minh Tú' },
    { id: 'QC_LEADER', dept: 'qc', lv: 'Leader', who: 'Nguyễn Thị Hoa' },
    { id: 'QC_MEMBER', dept: 'qc', lv: 'Member', who: 'Vũ Đức Anh' },
    { id: 'WAITING_LEADER', dept: 'waiting', lv: 'Leader', who: 'Hoàng Văn Bàn' },
    { id: 'WAITING_MEMBER', dept: 'waiting', lv: 'Member', who: 'Trịnh Thu Hà' },
    { id: 'PRODUCTION_LEADER', dept: 'prod', lv: 'Leader', who: 'Bùi Quang Chuyền' },
    { id: 'PRODUCTION_MEMBER', dept: 'prod', lv: 'Member', who: 'Ngô Thị Lan' },
    { id: 'WAREHOUSE_IN_LEADER', dept: 'wh_in', lv: 'Leader', who: 'Đặng Văn Nhập' },
    { id: 'WAREHOUSE_IN_MEMBER', dept: 'wh_in', lv: 'Member', who: 'Mai Thị Thành' },
    { id: 'PLANNER', dept: 'planner', lv: 'Điều độ', who: 'Lý Thanh Kế' }
  ];

  /* §9b.4 — Ma trận quyền.
     'full' = View + Accept + Edit · 'view' = chỉ xem · null = không thấy.
     Ba quy tắc: (1) ai cũng XEM được step 4; (2) Bàn team leader là
     ngoại lệ duy nhất có FULL trên step 4; (3) ngoài ra không thấy gì. */
  function quyen(deptId, step) {
    if (deptId === 'planner') return 'full';
    const d = DEPTS.find(x => x.id === deptId);
    if (d && d.step === step) return 'full';
    if (step === 4) return deptId === 'waiting' ? 'full' : 'view';
    return null;
  }

  /* ── Dữ liệu mẫu ────────────────────────────────────────────
     Mỗi MO đứng ở một chỗ khác nhau để không màn hình nào rỗng. */
  const MOS = [
    {
      code: 'M068828', sp: 'Tay cầm nhựa I', qty: 4000, pcsBox: 80, req: '1 giờ 40 phút',
      st: 'DRAFT', step: null, round: 1, done: 0, ng: 0
    },
    {
      code: 'M068821', sp: 'Nắp nhựa B', qty: 5000, pcsBox: 100, req: '1 giờ 30 phút',
      st: 'SUBMITTED', step: 0, round: 1, done: 0, ng: 0, sub: 'Chờ Kho xuất nhận'
    },
    {
      code: 'M068829', sp: 'Chốt hãm K', qty: 2500, pcsBox: 125, req: '50 phút',
      st: 'SUBMITTED', step: 0, round: 1, done: 0, ng: 0, sub: 'Chờ Kho xuất nhận'
    },
    {
      code: 'M068826', sp: 'Vòng bi G', qty: 1500, pcsBox: 0, req: '30 phút',
      st: 'PROCESSING', step: 0, round: 2, done: 0, ng: 0,
      rework: true, back: 'Kho', reason: 'Sai thông số setup',
      sub: 'QC FAIL vòng 1 — làm lại từ Kho'
    },
    {
      code: 'M068822', sp: 'Gioăng cao su C', qty: 2000, pcsBox: 250, req: '45 phút',
      st: 'PROCESSING', step: 0, round: 1, done: 0, ng: 0,
      accepted: '08:12', sub: 'Đã nhận — chờ bàn giao'
    },
    {
      code: 'M068823', sp: 'Trục thép D', qty: 8000, pcsBox: 50, req: '2 giờ 0 phút',
      st: 'PROCESSING', step: 1, round: 1, done: 0, ng: 0,
      accepted: '08:40', elapsed: '0 giờ 22 phút 14 giây', sub: 'Setup đang chỉnh máy'
    },
    {
      code: 'M068824', sp: 'Bạc đồng E', qty: 3000, pcsBox: 120, req: '1 giờ 0 phút',
      st: 'PROCESSING', step: 2, round: 1, done: 0, ng: 0,
      accepted: '09:02', elapsed: '0 giờ 08 phút 03 giây', sub: 'QC đang kiểm'
    },
    {
      code: 'M068825', sp: 'Lò xo F', qty: 12000, pcsBox: 500, req: '4 giờ 0 phút',
      st: 'PROCESSING', step: 3, round: 1, done: 0, ng: 0,
      accepted: '09:10', sub: 'QC PASS — chờ vào chuyền'
    },
    {
      code: 'M068820', sp: 'Vỏ máy bơm A', qty: 10000, pcsBox: 200, req: '3 giờ 0 phút',
      st: 'PROCESSING', step: 4, round: 2, done: 8000, ng: 200,
      back: 'Bàn team leader', lines: 'L01, L02', runSt: 'RUN',
      wait: '0 giờ 12 phút 40 giây', actual: '0 giờ 41 phút 05 giây',
      limit: '0 giờ 36 phút 00 giây', kpi: 'over', late: '0 giờ 05 phút 05 giây',
      /* §7b — hai nhánh song song, mỗi nhánh một mốc mở và một timer.
         Đóng thùng mở lúc 09:31, chỉ 7 phút sau khi line vào Đang lắp
         ráp — không phải chờ chốt sổ SX. */
      runStart: '09:24', packStart: '09:31',
      packTimer: '2 giờ 18 phút 00 giây', packBoxes: 9,
      sub: 'Vòng 2 — làm tiếp 2.000'
    },
    {
      code: 'M068827', sp: 'Ốc vít H', qty: 20000, pcsBox: 1000, req: '6 giờ 0 phút',
      st: 'PROCESSING', step: 4, round: 1, done: 0, ng: 0,
      lines: 'L05, L06, L07', runSt: 'HOLD', holdLine: 'L06', holdWhy: 'Hỏng khuôn ép — chờ thợ',
      wait: '0 giờ 31 phút 02 giây', actual: '1 giờ 48 phút 22 giây',
      limit: '6 giờ 00 phút 00 giây', kpi: 'ok',
      sub: 'Đang dừng L06'
    },
    {
      code: 'M068830', sp: 'Đế cao su J', qty: 6000, pcsBox: 150, req: '2 giờ 30 phút',
      st: 'PROCESSING', step: 4, round: 1, done: 0, ng: 0,
      lines: 'L09', runSt: 'DONE', packed: 5800,
      sxOk: 5800, sxNg: 120, sxShort: 80,
      ngWhy: 'Lỗi ép nhựa', shortWhy: 'Hết liệu cuối ca',
      wait: '0 giờ 09 phút 11 giây', actual: '2 giờ 21 phút 48 giây',
      limit: '2 giờ 30 phút 00 giây', kpi: 'ok',
      sub: 'Đã chốt sổ SX + đóng thùng — chờ Kho nhập'
    },
    {
      /* Đã nhận ở Kho nhập, chờ đếm rồi bấm Hoàn thành.
         8.400 + 450 + 150 = 9.000 = mục tiêu vòng → đúng ràng buộc §7.5.
         Đóng thùng 8.400 < 9.000 nên nút Hoàn thành sẽ đẩy về Bàn TL. */
      code: 'M068818', sp: 'Khớp nối N', qty: 9000, pcsBox: 300, req: '3 giờ 0 phút',
      st: 'PROCESSING', step: 5, round: 1, done: 0, ng: 0,
      packed: 8400, sxOk: 8400, sxNg: 450, sxShort: 150,
      ngWhy: 'Lỗi ren', shortWhy: 'Hết liệu cuối ca',
      accepted: '10:31', elapsed: '0 giờ 06 phút 12 giây',
      sub: 'Kho nhập đã nhận — chờ đếm lại'
    },
    {
      code: 'M068819', sp: 'Ống dẫn L', qty: 9000, pcsBox: 300, req: '3 giờ 0 phút',
      st: 'COMPLETED', step: 5, round: 1, done: 9000, ng: 150,
      sub: 'Hoàn thành 09:48'
    }
  ];

  /* §7.1 — 14 line. Trạng thái để vẽ lưới chọn line. */
  const LINES = [
    { n: 1, st: 'on', by: 'M068820' }, { n: 2, st: 'on', by: 'M068820' },
    { n: 3, st: 'free' }, { n: 4, st: 'free' },
    { n: 5, st: 'busy', by: 'M068827' }, { n: 6, st: 'stop', by: 'M068827' },
    { n: 7, st: 'busy', by: 'M068827' }, { n: 8, st: 'free' },
    { n: 9, st: 'busy', by: 'M068830' }, { n: 10, st: 'free' },
    { n: 11, st: 'free' }, { n: 12, st: 'free' },
    { n: 13, st: 'free' }, { n: 14, st: 'free' }
  ];

  /* §7.2b — hourly[] = {moId, round, moCode, day, slot, people, target,
     qty, note, at, by}, append-only. Bảng phải hiện đủ: bỏ `day` thì
     không phân biệt được cùng khung giờ của hai ngày, bỏ `at`/`by` thì
     không truy ra ai khai con số đó. */
  const HOURLY = [
    { day: '2026-09-16', slot: '13:00-14:00', mo: 'M068820', r: 2, people: 12, target: 600, qty: 248, note: 'Nghỉ giữa ca', at: '14:01', by: 'Bùi Quang Chuyền' },
    { day: '2026-09-16', slot: '11:00-12:00', mo: 'M068820', r: 2, people: 10, target: 500, qty: 512, note: '', at: '12:03', by: 'Ngô Thị Lan' },
    { day: '2026-09-16', slot: '10:00-11:00', mo: 'M068820', r: 2, people: 12, target: 600, qty: 583, note: 'Kẹt liệu 8 phút', at: '11:04', by: 'Ngô Thị Lan' },
    { day: '2026-09-16', slot: '09:00-10:00', mo: 'M068820', r: 2, people: 12, target: 600, qty: 640, note: 'Chạy ổn', at: '10:02', by: 'Ngô Thị Lan' },
    /* Hai dòng dưới CÙNG khung 02:00-03:00 nhưng KHÁC ngày — MO chạy
       qua đêm, cả hai đều hợp lệ. Đây là lý do khoá trùng phải gồm `day`. */
    { day: '2026-09-16', slot: '02:00-03:00', mo: 'M068827', r: 1, people: 8, target: 400, qty: 410, note: 'Ca đêm sang ngày mới', at: '03:06', by: 'Đỗ Văn Ca' },
    { day: '2026-09-15', slot: '02:00-03:00', mo: 'M068827', r: 1, people: 8, target: 400, qty: 380, note: 'Ca đêm', at: '03:04', by: 'Đỗ Văn Ca' }
  ];

  /* §7b.2 — packHourly[] = {moId, round, moCode, day, slot, boxes,
     pcsPerBox, note, at, by}. `pcsPerBox` phải là cột riêng: hai MO
     khác quy cách thì cùng "3 thùng" ra số pcs khác nhau. */
  const PACK_HOURLY = [
    { day: '2026-09-16', slot: '13:00-14:00', mo: 'M068820', r: 2, boxes: 2, pcsBox: 200, note: 'Thiếu thùng carton', at: '14:02', by: 'Ngô Thị Lan' },
    { day: '2026-09-16', slot: '11:00-12:00', mo: 'M068820', r: 2, boxes: 4, pcsBox: 200, note: '', at: '12:05', by: 'Ngô Thị Lan' },
    { day: '2026-09-16', slot: '10:00-11:00', mo: 'M068820', r: 2, boxes: 3, pcsBox: 200, note: 'Bắt đầu đóng', at: '11:06', by: 'Ngô Thị Lan' },
    { day: '2026-09-16', slot: '09:00-10:00', mo: 'M068830', r: 1, boxes: 6, pcsBox: 150, note: 'Quy cách 150 — khác M068820', at: '10:04', by: 'Trần Thị Mai' }
  ];

  /* §6b.4 — Bảng Các vòng của M068820 (gồm cả vòng đang chạy) */
  const ROUNDS = [
    {
      r: 1, from: 'Kho · 22:25', doneAt: '22:26', ok: 8000, ng: 200, short: 1800, packed: 8000,
      ngWhy: 'Lỗi ép nhựa', shortWhy: 'Chờ bù liệu', packNote: 'Đóng đủ hàng đạt',
      ret: 'Còn 2.000 — về Bàn team leader'
    },
    {
      r: 2, from: 'Bàn team leader · 09:18', doneAt: '—', ok: null, ng: null, short: null, packed: null,
      ngWhy: '—', shortWhy: '—', packNote: '—',
      ret: 'vòng chưa chốt sổ — số còn thay đổi', live: true
    }
  ];

  /* §9 [25A] — append-only, giữ vĩnh viễn. Mỗi action ghi đủ
     MO, round, step, action, user, timestamp, from→to, reason. */
  const LOG = [
    { day: '2026-09-16', at: '11:22', mo: 'M068826', r: 1, step: '2 · QC', act: 'QC_FAIL', by: 'Vũ Đức Anh', from: 'Step2 QC', to: 'Step0 Kho', note: 'Sai thông số setup → về Kho, vòng 2' },
    { day: '2026-09-16', at: '11:05', mo: 'M068824', r: 1, step: '2 · QC', act: 'STEP_2_ACCEPT', by: 'Nguyễn Thị Hoa', from: 'Step1 Setup', to: 'Step2 QC', note: 'Step1 auto-complete' },
    { day: '2026-09-16', at: '10:14', mo: 'M068827', r: 1, step: '4 · Sản xuất', act: 'RUN_HOLD', by: 'Bùi Quang Chuyền', from: 'RUN', to: 'WAIT', note: 'L06 dừng — hỏng khuôn ép' },
    { day: '2026-09-16', at: '10:02', mo: 'M068820', r: 2, step: '4 · Sản xuất', act: 'HOURLY_ADD', by: 'Ngô Thị Lan', from: '', to: '', note: '09:00-10:00 · 12 người · 600 → 640' },
    { day: '2026-09-16', at: '09:31', mo: 'M068820', r: 2, step: '4 · Đóng thùng', act: 'PACK_START', by: 'Ngô Thị Lan', from: '', to: '', note: 'Quy cách 200 pcs/thùng' },
    { day: '2026-09-16', at: '09:24', mo: 'M068820', r: 2, step: '4 · Sản xuất', act: 'RUN_START', by: 'Bùi Quang Chuyền', from: 'WAIT', to: 'RUN', note: 'L01, L02 → Đang lắp ráp' },
    { day: '2026-09-16', at: '09:21', mo: 'M068820', r: 2, step: '4 · Sản xuất', act: 'RUN_ADD', by: 'Bùi Quang Chuyền', from: 'Step3 Bàn TL', to: 'Step4 Sản xuất', note: 'Thêm L01, L02 · mốc vòng 2.000' },
    { day: '2026-09-16', at: '09:18', mo: 'M068820', r: 2, step: '3 · Bàn team leader', act: 'RETURN_BANCHO', by: 'Hệ thống', from: 'Step5 Kho nhập', to: 'Step3 Bàn TL', note: 'Nhập kho thiếu 2.000 → vòng 2' }
  ];

  /* §9 — Timer từng bước, cộng dồn qua mọi vòng */
  const TIMERS = [
    { step: '0 · Kho xuất', by: 'Trần Văn Kho', at: '08:00', dur: '0 giờ 25 phút 10 giây', n: 1 },
    { step: '1 · Setup máy', by: 'Phạm Hữu Sơn', at: '08:25', dur: '0 giờ 31 phút 42 giây', n: 1 },
    { step: '2 · QC', by: 'Nguyễn Thị Hoa', at: '08:57', dur: '0 giờ 11 phút 05 giây', n: 1 },
    { step: '3 · Bàn team leader', by: 'Hoàng Văn Bàn', at: '09:08', dur: '0 giờ 13 phút 20 giây', n: 2 },
    { step: '4 · Sản xuất', by: 'Bùi Quang Chuyền', at: '09:21', dur: '2 giờ 41 phút 05 giây', n: 2 },
    { step: '4 · Đóng thùng', by: 'Ngô Thị Lan', at: '09:31', dur: '2 giờ 18 phút 00 giây', n: 2 },
    { step: '5 · Kho nhập', by: 'Đặng Văn Nhập', at: '—', dur: '—', n: 1 }
  ];

  const QC_REASONS = ['Sai thông số setup', 'Lỗi khuôn/gá', 'Lỗi vật tư đầu vào', 'Lỗi lắp ráp', 'Khác'];

  /* 24 khung giờ, xếp vòng từ 06:00 (§7.2b) */
  const SLOTS = Array.from({ length: 24 }, (_, i) => {
    const a = (6 + i) % 24, b = (7 + i) % 24;
    return String(a).padStart(2, '0') + ':00-' + String(b).padStart(2, '0') + ':00';
  });

  const nf = n => (n == null) ? '—' : Number(n).toLocaleString('vi-VN');
  const at = step => MOS.filter(m => m.step === step && m.st === 'PROCESSING');

  return { DEPTS, ROLES, MOS, LINES, HOURLY, PACK_HOURLY, ROUNDS, LOG, TIMERS, QC_REASONS, SLOTS, quyen, nf, at };
})();
