/* ═══════════════════════════════════════════════════════════════
   app.js — Sidebar, điều hướng và phân quyền hiển thị
   Sidebar dựng lại theo vai đang đăng nhập: chỉ trạm của mình là
   thao tác được, Step 4 ai cũng xem, ngoài ra không thấy gì (§9b).
   ═══════════════════════════════════════════════════════════════ */
(function (M) {
  "use strict";

  const $ = s => document.querySelector(s);
  const dept = id => M.DEPTS.find(d => d.id === id);
  const role = () => M.ROLES.find(r => r.id === S.role);

  let S = { role: 'PRODUCTION_LEADER', route: 'prod/board' };

  /* Số trên badge của từng trạm — Kho đếm cả hai nhóm (§3) */
  function tonKho(id) {
    const d = dept(id);
    if (!d || d.step === null) return null;
    if (d.step === 0) return M.MOS.filter(m => m.step === 0).length;
    if (d.step === 4) return M.MOS.filter(m => m.step === 4).length;
    if (d.step === 5) return M.MOS.filter(m => m.runSt === 'DONE').length;
    return M.at(d.step).length;
  }

  /* ── Sidebar ─────────────────────────────────────────────── */
  function sidebar() {
    const r = role(), d = dept(r.dept);
    const initials = r.who.split(' ').slice(-2).map(x => x[0]).join('');

    const item = (route, ic, tx, ct, eye, hot) =>
      '<button class="sb-item' + (S.route === route ? ' on' : '') + '" data-nav="' + route + '">' +
      '<span class="ic">' + ic + '</span><span class="tx">' + tx + '</span>' +
      (eye ? '<span class="eye">chỉ xem</span>' : '') +
      (ct != null ? '<span class="ct' + (hot ? ' hot' : '') + '">' + ct + '</span>' : '') + '</button>';

    /* Nhóm 1 — trạm của mình, liệt kê đủ từng step của phòng ban */
    const mine = M.SCREENS[r.dept].map((s, i) =>
      item(r.dept + '/' + s.id, '<b class="mono" style="font-size:10px">' + (i + 1) + '</b>', s.nm,
        i === 0 ? tonKho(r.dept) : null, false, i === 0 && r.dept === 'wh_out')).join('');

    /* Nhóm 2 — xem chung. Step 4 gắn nhãn "chỉ xem" khi vai không có quyền ghi. */
    const canP4 = M.quyen(r.dept, 4) === 'full';
    let shared = item('shared/board', '📊', 'Bảng đang chạy', null, false);
    if (r.dept !== 'prod' && r.dept !== 'planner') {
      shared += item('shared/step4', '⚙️', 'Step 4 · Sản xuất', null, !canP4);
    }
    shared += item('shared/map', '🗺️', 'Luồng toàn quy trình', null, false);

    /* Nhóm 3 — tra cứu */
    const look = item('shared/trace', '🔎', 'Lịch sử &amp; Truy cứu', null, r.dept !== 'planner');

    return '<div class="sb-brand"><span class="logo">MES</span>' +
      '<span><b>MES v2.3</b><em>Mockup nghiệp vụ đã chốt</em></span></div>' +

      '<div class="sb-role"><div class="role-card">' +
      '<span class="av">' + initials + '</span>' +
      '<span class="who"><b>' + r.who + '</b><em>' + d.nm + ' · ' + r.lv + '</em></span></div>' +
      '<button class="sb-switch" data-act="roles"><span>Đổi vai để xem màn hình khác</span><span>⇅</span></button></div>' +

      '<nav class="sb-nav">' +
      '<div class="sb-group"><div class="gl">' + (d.step === null ? 'Điều độ' : 'Trạm của tôi · step ' + d.step) + '</div>' + mine + '</div>' +
      '<div class="sb-group"><div class="gl">Xem chung</div>' + shared + '</div>' +
      '<div class="sb-group"><div class="gl">Tra cứu</div>' + look + '</div>' +
      '</nav>';
  }

  /* ── Stepper của phòng ban ───────────────────────────────────
     Phòng ban thường: một dãy tuần tự, đánh số 1..n.
     Phòng có luồng rẽ nhánh (Sản xuất, §7b): dãy tuần tự ngắn rồi
     tách làn. Trong làn KHÔNG đánh số — số ngụ ý thứ tự, mà hai làn
     thì chạy cùng lúc, đánh số là nói sai. */
  function flowStrip(deptId, cur) {
    const list = M.SCREENS[deptId];
    const f = M.FLOW[deptId];

    const item = (s, n, sm) => s ? '<button class="flow-i' + (sm ? ' sm' : '') +
      (s.id === cur ? ' on' : '') + '" data-nav="' + deptId + '/' + s.id + '">' +
      (n ? '<span class="n">' + n + '</span>' : '') +
      '<span class="t"><b>' + s.nm + '</b><em>' + s.sub + '</em></span></button>' : '';

    if (!f) return '<div class="flow">' + list.map((s, i) => item(s, i + 1)).join('') + '</div>';

    const by = id => list.find(s => s.id === id);
    return '<div class="flow fork">' +
      '<div class="seq">' + f.seq.map((id, i) => item(by(id), i + 1)).join('') + '</div>' +
      '<div class="split"><em>song song</em></div>' +
      '<div class="lanes">' + f.lanes.map(l =>
        '<div class="lane"><span class="lane-lb">' + l.nm + '</span>' +
        l.ids.map(id => item(by(id), null, true)).join('') + '</div>').join('') +
      '</div></div>' +
      '<div class="note" style="margin:-8px 0 16px"><b>Ba bước đầu tuần tự; từ ' +
      '<code>Đang lắp ráp</code> thì hai nhánh chạy song song</b>, mỗi nhánh một timer riêng (§7b). ' +
      'Ràng buộc thứ tự <b>duy nhất</b> giữa hai nhánh: <code>Kết thúc đóng thùng</code> phải sau ' +
      '<code>Chốt sổ SX</code> — cái sản phẩm cuối ra khỏi chuyền thì mới đóng xong được. ' +
      'Step 4 sang Step 5 khi <b>cả hai nhánh</b> đã kết thúc.</div>';
  }

  /* ── Bản đồ luồng — trả lời "quy trình đi đâu về đâu" ────── */
  function mapView() {
    const box = (d, note) => {
      const n = tonKho(d.id);
      return '<button class="sb-item" data-nav="' + d.id + '/' + M.SCREENS[d.id][0].id + '" ' +
        'style="border:1px solid var(--line);background:var(--surface);padding:12px;margin-bottom:8px">' +
        '<span class="ic" style="font-size:16px">' + d.ic + '</span>' +
        '<span class="tx"><b style="display:block;color:var(--ink);font-size:13px">' +
        (d.step !== null ? 'Step ' + d.step + ' · ' : '') + d.full + '</b>' +
        '<em style="display:block;font-size:11px;color:var(--ink-3);font-style:normal">' + note + '</em></span>' +
        (n != null ? '<span class="ct">' + n + '</span>' : '') + '</button>';
    };
    const chain = M.DEPTS.filter(d => d.step !== null);
    return '<div class="pg-head"><span class="kicker">Luồng</span>' +
      '<h1>Toàn quy trình — ai làm gì, ở đâu</h1>' +
      '<p>Bấm một trạm để mở màn hình của phòng ban đó. Con số bên phải là tồn đang chờ tại trạm.</p></div>' +
      '<div class="cols c2"><div>' +
      M.ui.panel('Đường đi chính', '6 phòng ban',
        chain.map((d, i) => box(d, [
          'Nhận lệnh · bàn giao xuống xưởng · cũng là nơi MO QC FAIL quay về',
          'Chỉnh máy — không bấm Complete, QC quét là tự đóng',
          'PASS → Bàn team leader · FAIL → về Kho, vòng mới',
          'Chờ vào chuyền — và là nơi MO thiếu SL quay về',
          'Chạy 14 line + đóng thùng song song, hai timer riêng',
          'Đếm lại, chốt đơn — đủ thì COMPLETED, thiếu thì trả về Bàn TL'
        ][i])).join('')) +
      '</div><div>' +
      M.ui.panel('Hai đường quay lại', 'khác nhau ở nguyên nhân',
        '<div class="note warn"><b>Thiếu SL · line dừng quá lâu → về Bàn team leader.</b> ' +
        'Máy setup đúng, hàng đã qua QC — chỉ thiếu số. Không in lại phiếu, không setup lại, không QC lại.</div>' +
        '<div class="note bad"><b>QC FAIL → về Kho.</b> Setup sai nên phải làm lại từ gốc. ' +
        'Cho về Bàn team leader thì MO <b>nhảy qua luôn Setup và QC</b> — hàng lỗi setup đi thẳng vào chuyền mà không ai sửa máy.</div>' +
        '<div class="note">Cả hai đi qua <b>một hàm duy nhất</b> <code>moVongMoi(mo, lý do, bướcVề)</code> ' +
        'để <code>round</code>, badge và history luôn nhất quán.</div>') +
      M.ui.panel('Quy tắc đọc mã quét', '§1b.2 · §1b.3', M.ui.scanRules) +
      M.ui.panel('Quy ước UX xuyên suốt', 'vì sao màn hình trông như vậy',
        '<div class="note"><b>1 · Nhận bằng quét, không bấm Accept.</b> Nút Accept trên từng dòng hàng đợi đã bỏ — ' +
        'nhiều đơn cùng lúc thì bấm rất dễ trúng nhầm MO bên cạnh. Ô quét đứng đầu trang <b>Quét nhận</b>, ' +
        'ngay trên hàng đợi mà nó tác động, và phản hồi hiện ngay trong ô. Riêng Kho giữ thêm nút cả lô (§1b.4).</div>' +
        '<div class="note"><b>2 · Step N đóng khi Step N+1 nhận.</b> Bước 1→3 không có nút Complete. ' +
        'Chỉ Step4 và Step5 có nút riêng vì cần đo timer song song.</div>' +
        '<div class="note"><b>3 · Sidebar là bản đồ quyền.</b> Trạm của mình liệt kê đủ từng step; ' +
        'Step 4 ai cũng thấy nhưng gắn nhãn <i>chỉ xem</i> nếu không có quyền ghi; ngoài ra không có mục nào khác.</div>' +
        '<div class="note"><b>4 · Mọi con số chỉ nói về vòng hiện tại.</b> Line, KPI, thời gian, sản lượng giờ ' +
        'đều lọc theo <code>round</code>. Chỗ nào cộng dồn mọi vòng thì ghi rõ (bảng Timer, qtyDone).</div>') +
      '</div></div>';
  }

  /* ── Màn chặn quyền ──────────────────────────────────────── */
  function denied(d) {
    return '<div class="pg-head"><span class="kicker" style="background:var(--bad-bg);color:var(--bad)">Không có quyền</span>' +
      '<h1>' + d.full + '</h1></div>' +
      M.ui.panel('Vai hiện tại không mở được màn hình này', '§9b.4',
        '<div class="note bad"><b>Ngoài step của mình và Step 4, không thấy gì.</b> ' +
        'QC không mở được màn hình Kho, Kho không mở được màn hình QC.</div>' +
        '<div class="note">Đây là mockup nên mục này vẫn bấm tới được để bạn thấy màn hình chặn trông ra sao. ' +
        'Trong bản chạy thật, sidebar sẽ không liệt kê nó.</div>' +
        '<div class="btnrow" style="margin-top:12px">' +
        '<button class="btn primary" data-act="roles">Đổi sang vai của ' + d.nm + '</button></div>');
  }

  /* ── Render ──────────────────────────────────────────────── */
  function render() {
    $('#sb').innerHTML = sidebar();

    const r = role();
    const [a, b] = S.route.split('/');
    let html, crumb;

    if (a === 'shared') {
      const t = { board: 'Bảng đang chạy', step4: 'Step 4 · Sản xuất', map: 'Luồng toàn quy trình', trace: 'Lịch sử & Truy cứu' }[b];
      crumb = 'Xem chung <b>›</b> ' + t;
      if (b === 'board') {
        html = '<div class="pg-head"><span class="kicker">Xem chung</span><h1>Bảng đang chạy</h1>' +
          '<p>Hiện MO ở mọi step, mọi phòng ban đều xem được — bảng tổng quan để cả xưởng biết đơn hàng đang tới đâu.</p></div>' +
          M.runBoard(M.quyen(r.dept, 4) === 'full');
      } else if (b === 'step4') html = M.step4View();
      else if (b === 'map') html = mapView();
      else {
        html = '<div class="pg-head"><span class="kicker">Tra cứu</span><h1>Truy cứu MO · M068820</h1>' +
          '<p>Bốn tầng: các vòng → đi qua các bước → năng suất line &amp; sản lượng giờ → nhật ký đầy đủ.</p></div>' +
          M.traceView();
      }
    } else {
      const d = dept(a);
      const q = M.quyen(r.dept, d.step);
      crumb = d.full + ' <b>›</b> ' + (M.SCREENS[a].find(s => s.id === b) || {}).nm;
      if (q === null && a !== r.dept) {
        html = denied(d);
      } else {
        const sc = M.SCREENS[a].find(s => s.id === b) || M.SCREENS[a][0];
        html = '<div class="pg-head"><span class="kicker">' + d.ic + ' ' +
          (d.step !== null ? 'Step ' + d.step + ' · ' : '') + d.full + '</span>' +
          '<h1>' + sc.nm + '</h1><p>' + d.desc + ' — ' + d.at + '.</p></div>' +
          flowStrip(a, sc.id) +
          (q === 'view' ? '<div class="note warn" style="margin:0 0 16px">👁 <b>Chỉ xem.</b> ' +
            'Vai <b>' + dept(r.dept).nm + '</b> xem được step này nhưng không bấm được gì.</div>' : '') +
          '<div class="' + (q === 'view' ? 'readonly' : '') + '">' + sc.render() + '</div>';
      }
    }

    $('#crumb').innerHTML = crumb;
    $('#view').innerHTML = html;
    window.scrollTo(0, 0);
    bindLive();
    paintScan();
  }

  /* ── Kiểm tra sống trong form chốt sổ (§7.5 · §7b) ───────── */
  function bindLive() {
    const ok = $('#sx-ok'), ng = $('#sx-ng'), sh = $('#sx-short'), out = $('#sx-sum');
    if (out) {
      const TARGET = 2000;
      const calc = () => {
        const s = (+ok.value || 0) + (+ng.value || 0) + (+sh.value || 0);
        const d = s - TARGET;
        out.className = 'note ' + (d === 0 ? 'ok' : 'bad');
        out.innerHTML = d === 0
          ? '<b>Σ ' + M.nf(s) + ' — khớp mục tiêu vòng.</b> Cho phép chốt sổ.'
          : '<b>Σ ' + M.nf(s) + '/' + M.nf(TARGET) + ' — đang ' + (d > 0 ? 'dư ' : 'hụt ') + M.nf(Math.abs(d)) +
          '.</b> Chặn, không cho chốt sổ — có hàng không ai khai.';
      };
      [ok, ng, sh].forEach(i => i.addEventListener('input', calc));
      calc();
    }
    const pq = $('#pk-qty'), po = $('#pk-sum');
    if (po) {
      const SXOK = 5800;
      const calc = () => {
        const v = +pq.value || 0;
        po.className = 'note ' + (v > SXOK ? 'bad' : v === SXOK ? 'ok' : 'warn');
        po.innerHTML = v > SXOK
          ? '<b>Vượt SL đạt của Sản xuất (' + M.nf(SXOK) + ').</b> Chặn — không đóng được nhiều hơn hàng làm ra.'
          : v === SXOK
            ? '<b>Khớp SL đạt ' + M.nf(SXOK) + '.</b> Đóng hết hàng đạt.'
            : '<b>Đóng ' + M.nf(v) + '/' + M.nf(SXOK) + ' — còn ' + M.nf(SXOK - v) + ' hàng đạt chưa đóng.</b> ' +
            'Vẫn cho qua, nhưng ghi cảnh báo vào PACK_COMPLETE.';
      };
      pq.addEventListener('input', calc);
      calc();
    }
  }

  /* ── Modal đổi vai ───────────────────────────────────────── */
  function rolesModal() {
    const grp = (title, list) => '<div class="gl">' + title + '</div><div class="rolegrid">' +
      list.map(r => {
        const d = dept(r.dept);
        return '<button class="rolebtn' + (r.id === S.role ? ' on' : '') + '" data-role="' + r.id + '">' +
          '<span class="av">' + d.ic + '</span><span class="who"><b>' + d.nm + ' · ' + r.lv + '</b>' +
          '<em>' + r.who + '</em></span></button>';
      }).join('') + '</div>';
    $('#rolebody').innerHTML =
      grp('6 phòng ban × 2 cấp', M.ROLES.filter(r => r.dept !== 'planner')) +
      grp('Vai điều độ', M.ROLES.filter(r => r.dept === 'planner')) +
      '<div class="note"><b>Hiện Leader và Member có quyền y hệt nhau.</b> Vẫn tách sẵn từ đầu vì sau này ' +
      'chắc chắn phải siết (chỉ Leader được chốt sổ, chỉ Leader được huỷ thao tác đã nhận). ' +
      'Tách sau thì phải sửa dữ liệu của mọi tài khoản đang chạy; tách sẵn thì chỉ đổi một dòng kiểm tra.</div>' +
      '<div class="note warn"><b>Còn chưa chốt (§9b.8):</b> Leader khác Member ở chỗ nào, ' +
      'và có cần vai chỉ-xem cho quản lý cấp trên không.</div>';
    $('#ov').hidden = false;
  }

  /* Nạp mã vào ô quét thay vì nhận luôn — bấm một dòng hàng đợi vẫn
     phải là thao tác có chủ đích, không phải một cú bấm là xong (§1b.1) */
  function nap(code, tien) {
    const s = $('#scan');
    if (!s) return toast('Trang này không có ô quét.', true);
    s.value = code;
    s.focus();
    toast((tien || 'Đã nạp ') + code + ' vào ô quét — bấm Nhận để xác nhận.');
  }

  /* Khung ngắm camera. Mockup không mở camera thật: liệt kê đúng các
     MO đang hiện trong hàng đợi để bấm thử cho ra luồng. */
  function camModal() {
    const codes = queueCodes();
    $('#camchips').innerHTML = codes.length
      ? codes.map(c => '<button data-camcode="' + c + '">' + c + '</button>').join('')
      : '<span class="dim" style="font-size:12px">Hàng đợi trạm này đang trống.</span>';
    $('#cam').hidden = false;
  }

  let tt;
  function toast(m, err) {
    const t = $('#toast');
    t.textContent = m; t.className = err ? 'err' : ''; t.hidden = false;
    clearTimeout(tt); tt = setTimeout(() => { t.hidden = true; }, 3200);
  }

  /* ── Sự kiện ─────────────────────────────────────────────── */
  document.addEventListener('click', e => {
    const nav = e.target.closest('[data-nav]');
    if (nav) { S.route = nav.getAttribute('data-nav'); render(); return; }

    const go = e.target.closest('[data-go]');
    if (go) { S.route = go.getAttribute('data-go'); render(); return; }

    const rb = e.target.closest('[data-role]');
    if (rb) {
      S.role = rb.getAttribute('data-role');
      const d = dept(role().dept);
      S.route = role().dept + '/' + M.SCREENS[role().dept][0].id;
      /* Đổi vai là đổi trạm — phản hồi của trạm cũ không mang theo */
      lastFb = null; lastOk = null;
      $('#ov').hidden = true;
      render();
      toast('Đang xem bằng vai ' + d.nm + ' · ' + role().lv);
      return;
    }

    /* §1b.1 — bấm một dòng hàng đợi để nạp mã vào ô quét */
    const pick = e.target.closest('[data-pick]');
    if (pick) { nap(pick.getAttribute('data-pick')); return; }

    /* Camera "đọc" được một mã — mockup nên chọn từ danh sách */
    const cc = e.target.closest('[data-camcode]');
    if (cc) {
      $('#cam').hidden = true;
      nap(cc.getAttribute('data-camcode'), 'Camera đọc được ');
      return;
    }

    const act = e.target.closest('[data-act]');
    if (!act) return;
    const a = act.getAttribute('data-act');
    if (a === 'roles') rolesModal();
    else if (a === 'cam') camModal();
    else if (a === 'cam-close') $('#cam').hidden = true;
    else if (a === 'close') $('#ov').hidden = true;
    else if (a === 'theme') {
      const cur = document.documentElement.getAttribute('data-theme');
      document.documentElement.setAttribute('data-theme', cur === 'dark' ? 'light' : 'dark');
    } else if (a === 'scan') nhan();
  });

  /* Đầu đọc USB gõ xong là bắn Enter — phải nhận được, nếu không thì
     mỗi lần quét vẫn phải với tay bấm nút, mất hết cái lợi của đầu đọc. */
  document.addEventListener('keydown', e => {
    if (e.key === 'Enter' && e.target && e.target.id === 'scan') { e.preventDefault(); nhan(); }
  });

  /* ── Phản hồi khi quét ───────────────────────────────────────
     Nằm ngay trong thanh quét, một dòng, sát chỗ vừa gõ. §1b.3 chốt
     "quét sai trạm phải báo rõ lý do, không im lặng" nên không bỏ
     được — nhưng cũng không đáng một panel riêng chiếm nửa màn hình. */
  let lastFb = null, lastOk = null;

  function paintScan() {
    const fb = $('#fb');
    if (!fb) return;
    fb.innerHTML = lastFb
      ? '<div class="scanfb ' + (lastFb.ok ? 'ok' : 'err') + '">' +
      '<span class="ic">' + (lastFb.ok ? '✓' : '✕') + '</span>' +
      '<span><b>' + lastFb.head + '</b> · ' + lastFb.msg + '</span></div>'
      : '';
  }

  /* Ghi kết quả một lần quét. Lỗi bắn thêm toast: tay người quét đang
     ở đầu đọc, mắt ở cái tem trên thùng hàng — đường hỏng là đường
     không được phép bỏ sót, nên chịu lặp một lần. */
  function ghi(ok, code, head, msg) {
    lastFb = { ok, head, msg };
    if (ok) {
      lastOk = code;
      const el = $('#scan'); if (el) el.value = '';
    } else toast(head, true);
    paintScan();
    return ok;
  }

  function nhan() {
    const el = $('#scan');
    const v = ((el && el.value) || '').trim();
    if (!v) return ghi(false, null, 'Chưa có mã để nhận', 'Ô quét đang trống.');

    /* Đọc mã đúng luật §1b.2 để mockup cũng từ chối được đúng chỗ */
    const t = v.toUpperCase().replace(/\s+/g, '');
    let hits = [...new Set(t.match(/M\d{6}(?!\d)/g) || [])];

    /* Không ra mã nào thì thử sửa nhầm O↔0, I/L↔1 trong 6 ký tự sau chữ M.
       Vẫn phải khớp đúng 6 chữ số sau khi sửa, nếu không thì bỏ. */
    if (!hits.length) {
      for (const u of (t.match(/M[A-Z0-9]{6}(?![A-Z0-9])/g) || [])) {
        const sua = 'M' + u.slice(1).replace(/O/g, '0').replace(/[IL]/g, '1');
        if (/^M\d{6}$/.test(sua)) hits.push(sua);
      }
      hits = [...new Set(hits)];
    }

    if (hits.length > 1) {
      return ghi(false, v, 'Quét ra nhiều mã — quét lại',
        'Đọc được ' + hits.join(' · ') + ' trong một lần quét. Thà bắt quét lại còn hơn đoán sai đơn.');
    }
    if (!hits.length) {
      return ghi(false, v, 'Không đọc được mã MO',
        'Chuỗi "' + v + '" không chứa mã hợp lệ (M + đúng 6 chữ số).');
    }

    const mo = M.MOS.find(m => m.code === hits[0]);
    if (!mo) {
      return ghi(false, hits[0], hits[0] + ' — không có trong hệ thống',
        'Mã đọc được nhưng không khớp MO nào.');
    }

    /* Nhận được hay không thì soi theo HÀNG ĐỢI đang hiện, không so
       mo.step với step của trạm: hàng đợi Kho nhập toàn MO còn đứng ở
       step 4 (đã đóng thùng xong nhưng chưa ai nhận), so theo step thì
       lô nào về kho cũng bị từ chối. */
    const tram = dept(role().dept).nm;
    const q = queueCodes();

    /* Chống bắn hai lần: khoá theo mã + trạm, không chỉ theo mã (§1b.3).
       lastOk reset khi đổi vai, nên cùng MO quét tiếp ở trạm kế bên vẫn ăn ngay. */
    if (lastOk === mo.code) {
      return ghi(false, mo.code, mo.code + ' — đã nhận ở trạm này rồi',
        'Đầu đọc hay bắn trùng. Lần trùng trong 2 giây bị bỏ qua, không tạo bản ghi thứ hai.');
    }

    if (q.length && q.indexOf(mo.code) < 0) {
      const oDau = (M.DEPTS.find(x => x.step === mo.step) || {}).nm || 'nơi khác';
      return ghi(false, mo.code, mo.code + ' — đang ở ' + oDau + ', không nhận được ở đây',
        'Quét sai trạm phải báo rõ lý do, không im lặng.');
    }

    return ghi(true, mo.code, mo.code + ' — ' + tram + ' đã nhận',
      mo.sp + ' · ' + M.nf(mo.qty - mo.done) + ' pcs. Timer bước này bắt đầu chạy.');
  }

  /* Các mã đang nằm trong hàng đợi hiển thị trên trang */
  function queueCodes() {
    if (!document.querySelectorAll) return [];
    return [...new Set([...document.querySelectorAll('#view [data-pick]')].map(n => n.getAttribute('data-pick')))];
  }

  $('#ov').addEventListener('click', e => { if (e.target.id === 'ov') $('#ov').hidden = true; });
  $('#cam').addEventListener('click', e => { if (e.target.id === 'cam') $('#cam').hidden = true; });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { $('#ov').hidden = true; $('#cam').hidden = true; }
  });

  /* Giờ xưởng */
  setInterval(() => {
    const d = new Date();
    $('#clock').textContent = String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
  }, 1000);
  $('#clock').textContent = '—:—';

  render();
})(window.MES);
