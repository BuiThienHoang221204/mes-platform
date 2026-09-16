/* ═══════════════════════════════════════════════════════════════
   screens.js — Mockup từng trang, từng step của từng phòng ban
   Mỗi phòng ban là một "luồng" gồm nhiều step; stepper trên đầu
   trang đi qua đúng thứ tự người vận hành làm ngoài xưởng.
   ═══════════════════════════════════════════════════════════════ */
(function (M) {
  "use strict";
  const nf = M.nf, at = M.at;

  /* ── Mảnh dùng lại ──────────────────────────────────────── */
  /* act — nút thao tác trên chính header của panel. Bulk action của
     một danh sách thuộc về thanh đầu danh sách, không phải một panel
     riêng bên cạnh. */
  const panel = (title, meta, body, flush, act) =>
    '<section class="panel"><header><h2>' + title + '</h2>' +
    (meta ? '<span class="meta">' + meta + '</span>' : '') +
    (act ? '<span class="hact">' + act + '</span>' : '') + '</header>' +
    '<div class="body' + (flush ? ' flush' : '') + '">' + body + '</div></section>';

  const empty = (ic, t, s) =>
    '<div class="empty"><div class="e-ic">' + ic + '</div><b>' + t + '</b><em>' + s + '</em></div>';

  const tbl = (cols, rows) =>
    '<div class="tw"><table class="t"><thead><tr>' +
    cols.map(c => '<th' + (c.num ? ' class="num"' : '') + '>' + c.t + '</th>').join('') +
    '</tr></thead><tbody>' + rows + '</tbody></table></div>';

  /* Badge của MO — vòng, rework, tiến độ cộng dồn (§6b.4) */
  function badges(mo) {
    const b = [];
    if (mo.round > 1) b.push('<span class="bdg warn">Vòng ' + mo.round + '</span>');
    if (mo.rework) b.push('<span class="bdg bad">Rework · QC FAIL</span>');
    if (mo.done > 0) b.push('<span class="bdg">Đã xong ' + nf(mo.done) + ' · Còn ' + nf(mo.qty - mo.done) + '</span>');
    if (mo.pcsBox === 0) b.push('<span class="bdg line">Không đóng thùng</span>');
    return b.join(' ');
  }

  /* Dòng hàng đợi — bấm vào là nạp mã vào ô quét (§1b.1) */
  function qrow(mo, extra) {
    return '<div class="qrow" data-pick="' + mo.code + '">' +
      '<span class="code">' + mo.code + '</span>' +
      '<span class="nm"><b>' + mo.sp + '</b><em>' + (mo.sub || '') + '</em></span>' +
      '<span class="tags">' + badges(mo) + '</span>' +
      '<span class="qty">' + nf(mo.qty - mo.done) + '<em>' + (mo.done > 0 ? 'còn lại' : 'pcs kế hoạch') + '</em></span>' +
      (extra || '') + '</div>';
  }

  const queueList = (list, ex) => list.length
    ? list.map(m => qrow(m, ex)).join('')
    : empty('✓', 'Hàng đợi trống', 'Chưa có lệnh nào chờ ở trạm này.');

  /* Bảng "Đang ở bước N" — MO đã nhận tại trạm và timer bước đang chạy.
     Dùng chung một khung cho mọi trạm để nhìn quen mắt: lệnh nào đang
     nằm trong tay mình, nhận lúc mấy giờ, trôi bao lâu rồi. Hàng đợi
     trả lời "sắp phải làm gì", bảng này trả lời "đang giữ cái gì". */
  function dangO(n, o) {
    o = o || {};
    const list = at(n);
    const tram = (M.DEPTS.find(d => d.step === n) || {}).nm || '';
    const rows = list.map(m =>
      '<tr class="hl"><td class="mono"><b>' + m.code + '</b></td>' +
      '<td>' + m.sp + '</td>' +
      '<td class="num">' + nf(m.qty - m.done) + '</td>' +
      '<td class="mono">' + m.req + '</td>' +
      '<td class="mono">' + (m.accepted || '—') + ' · ' + tram + '</td>' +
      '<td class="mono">' + (m.elapsed || '—') + '</td>' +
      '<td>' + (badges(m) || '<span class="dim">—</span>') + '</td>' +
      '<td class="right">' + (o.act ? o.act(m) : '') + '</td></tr>').join('');
    return panel(o.title || ('Đang ở bước ' + n), list.length + ' MO',
      tbl([{ t: 'MO' }, { t: 'Tên con hàng' }, { t: 'SL cần làm', num: 1 }, { t: 'TG yêu cầu Step4' },
      { t: 'Nhận lúc' }, { t: 'Timer bước ' + n }, { t: 'Ghi chú' }, { t: '' }],
        rows || '<tr><td colspan="8">' +
        empty('⏳', 'Không có MO nào đang ở bước này', 'Quét nhận ở bước trước đã.') + '</td></tr>'), true);
  }

  const QR_ICON = '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" ' +
    'stroke-width="2" stroke-linecap="round" aria-hidden="true">' +
    '<path d="M3 8V5a2 2 0 0 1 2-2h3M16 3h3a2 2 0 0 1 2 2v3M21 16v3a2 2 0 0 1-2 2h-3M8 21H5a2 2 0 0 1-2-2v-3"/>' +
    '<path d="M3 12h18"/></svg>';

  /* Câu nhắc dưới ô quét — mỗi trạm một việc khác nhau, nên
     không dùng chung một câu chung chung cho cả sáu phòng ban. */
  const SCAN_HINT = {
    wh_out: 'Quét QR để Kho nhận lệnh. Phát lệnh đầu ca thì dùng nút <b>Accept tất cả</b> (§7A).',
    setup: 'Quét QR để Setup nhận. Chỉ nhận được lệnh đã bàn giao từ Kho (§4).',
    qc: 'Quét QR để QC nhận — Step1 của Setup tự đóng cùng lúc (§5).',
    waiting: 'Quét QR để Bàn team leader nhận — Step2 của QC tự đóng (§6).',
    prod: 'Quét QR để nhận MO vào chuyền, rồi chọn line ở bước kế tiếp (§7.1).',
    wh_in: 'Quét QR để Kho nhập nhận. Chỉ hiện lô đã kết thúc đóng thùng (§8).'
  };

  /* Ba đường vào gộp vào một ô: gõ tay · đầu đọc USB bắn thẳng vào
     input · nút Camera cho máy không có đầu đọc. */
  function scanBar(deptId) {
    return '<div class="scanbar"><div class="row">' +
      '<input id="scan" placeholder="Quét / nhập MO Code…" autocomplete="off" spellcheck="false">' +
      '<button class="btn btn-cam" data-act="cam">' + QR_ICON + 'Camera</button>' +
      '<button class="btn primary" data-act="scan">Nhận</button>' +
      '</div><div id="fb"></div>' +
      '<div class="hint">' + SCAN_HINT[deptId] + '</div></div>';
  }

  /* Trang "Quét nhận" của mọi trạm — một cột, xếp dọc theo đúng thứ
     tự làm việc: quét → nhìn hàng đợi → đọc ghi chú nếu cần.

     Không có cột phải. Hàng đợi là thứ người ta nhìn lâu nhất ở trạm
     này nên cho nó cả bề ngang; nhét chú thích sang bên cạnh thì hàng
     đợi bị bóp còn nửa màn hình để lấy chỗ cho chữ không ai đọc lại
     lần thứ hai. Quy tắc đọc mã gom về trang "Luồng toàn quy trình". */
  function scanPage(o) {
    const q = o.queue();
    return scanBar(o.dept) +
      (o.tiles || '') +
      panel(o.qTitle || 'Hàng đợi', q.length + ' lệnh',
        o.qBody ? o.qBody(q) : queueList(q), true, o.act) +
      (o.notes || '');
  }

  const scanRules =
    '<div class="note"><b>Quy tắc đọc mã (§1b.2).</b> Mã MO là <code>M</code> + đúng 6 chữ số. ' +
    'Bỏ mọi ký tự đứng trước chữ <code>M</code>: <code>XM068820</code> → <code>M068820</code>. ' +
    'Tự sửa <code>O</code>→<code>0</code>. <b>Từ chối</b> khi quét ra 7 chữ số hoặc nhiều mã một lần — ' +
    'cắt bừa ra một mã có thật là loại lỗi không ai phát hiện được.</div>' +
    '<div class="note">Chống bắn hai lần: bỏ qua lần trùng trong 2 giây, khoá theo <b>mã + trạm</b> ' +
    'chứ không chỉ theo mã — cùng MO quét tiếp ở trạm kế bên vẫn phải ăn ngay.</div>';

  /* ═══════════════════════════════════════════════════════════
     0 · KHO XUẤT — Bàn giao vật tư xuống xưởng (§3)
     ═══════════════════════════════════════════════════════════ */
  const WH_OUT = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        const q = () => M.MOS.filter(m => m.step === 0 && !m.accepted);
        const held = M.MOS.filter(m => m.step === 0 && m.accepted);
        return scanPage({
          dept: 'wh_out', queue: q, qTitle: 'Hàng đợi Kho xuất',
          tiles: '<div class="tiles" style="margin-bottom:16px">' +
            tile('Chờ nhận', q().length, 'lệnh mới + trả về', 'acc') +
            tile('Đã nhận, chưa giao', held.length, 'còn nằm ở kho', 'warn') +
            tile('Đã giao hôm nay', 6, 'xuống Setup', 'ok') +
            tile('Trong đó Rework', q().filter(m => m.rework).length, 'QC FAIL trả về', 'bad') +
            '</div>',
          /* §1b.4 — Kho là chỗ duy nhất còn thao tác hàng loạt, nên hai
             nút này đứng ngay trên đầu danh sách mà chúng tác động. */
          act: '<button class="btn sm primary">Accept tất cả (' + q().length + ')</button>' +
            '<button class="btn sm">Bàn giao tất cả (' + held.length + ')</button>',
          notes: '<div class="note"><b>Riêng Kho giữ cả hai cách nhận.</b> Quét từng lệnh khi cần chính xác, ' +
            'và hai nút cả lô ở đầu danh sách khi phát lệnh đầu ca — §7A chốt Kho phải xử được 10–100 lệnh một lúc. ' +
            'Đây là <b>ngoại lệ duy nhất</b>; mọi bước khác đã bỏ nút Accept trên từng dòng vì nhiều đơn cùng lúc ' +
            'thì bấm rất dễ trúng nhầm MO bên cạnh.</div>' +
            '<div class="note"><b>Badge trên thanh trạm đếm cả hai nhóm</b> — lệnh chưa ai nhận, và lệnh ' +
            'đã nhận nhưng chưa bàn giao. Chỉ đếm nhóm đầu thì badge hiện <code>0</code> trong khi kho còn hàng chờ giao.</div>' +
            '<div class="note warn"><b>MO quay về do QC FAIL không hiện như lệnh mới.</b> ' +
            'Dòng <code>M068826</code> mang badge <code>Rework</code> + <code>Vòng 2</code> và ghi rõ lý do FAIL — ' +
            'người kho phải biết đây là hàng làm lại để lấy đúng vật tư bù.</div>'
        });
      }
    },
    {
      id: 'handover', nm: 'Bàn giao', sub: 'Giao xuống Setup',
      render() {
        const held = M.MOS.filter(m => m.step === 0 && m.accepted);
        const rows = held.map(m =>
          '<tr><td class="mono"><b>' + m.code + '</b></td><td>' + m.sp + '</td>' +
          '<td class="num">' + nf(m.qty) + '</td><td class="mono">' + m.accepted + '</td>' +
          '<td>' + badges(m) + '</td>' +
          '<td class="right"><div class="btnrow" style="justify-content:flex-end">' +
          '<button class="btn sm" data-go="wh_out/slip">Xem phiếu</button>' +
          '<button class="btn sm primary">Bàn giao</button></div></td></tr>').join('');
        return panel('Đã nhận — chờ bàn giao xuống Setup', held.length + ' lệnh',
          tbl([{ t: 'MO' }, { t: 'Tên con hàng' }, { t: 'Số lượng', num: 1 }, { t: 'Nhận lúc' }, { t: 'Ghi chú' }, { t: '' }],
            rows || '<tr><td colspan="6">' + empty('📦', 'Không có lệnh nào', 'Nhận lệnh ở bước trước đã.') + '</td></tr>'), true) +
          '<div class="note"><b>Đúng hai thao tác: nhận và bàn giao.</b> Ghi riêng mỗi MO ' +
          '<code>acceptedBy/At</code> và <code>handedOverBy/At</code>. Chưa <code>HANDOVER</code> thì Setup không nhận được — ' +
          'đây là chặn cứng, không phải nhắc nhở.</div>' +
          '<div class="note ok"><b>Đã bỏ bước In phiếu.</b> Lô 50 lệnh một ca là bớt 50 thao tác. ' +
          'Cái bấm đó không quyết định điều gì — in hay không thì hàng vẫn xuống xưởng.</div>';
      }
    },
    {
      id: 'slip', nm: 'Xem phiếu', sub: 'Tra cứu — không ghi sổ',
      render() {
        return '<div class="cols c2"><div>' +
          panel('Phiếu M068826 · bản in trình duyệt', '§3 · phiếu [5]',
            '<div class="slip"><div class="big">M068826</div>' +
            '<div class="qr" aria-hidden="true"></div>' +
            '<dl><dt>Tên con hàng</dt><dd>Vòng bi G</dd>' +
            '<dt>Số lượng</dt><dd class="mono">1.500 pcs</dd>' +
            '<dt>TG yêu cầu Step4</dt><dd class="mono">30 phút</dd>' +
            '<dt>Quy cách</dt><dd>Không đóng thùng</dd>' +
            '<dt>SL còn thiếu</dt><dd class="mono">1.500</dd>' +
            '<dt>Số lần trả lại</dt><dd>1 · QC FAIL</dd></dl></div>' +
            '<div class="btnrow" style="margin-top:14px"><button class="btn">In bằng trình duyệt</button></div>') +
          '</div><div>' +
          panel('Vì sao phiếu tách khỏi quy trình', null,
            '<div class="note"><b><code>Xem phiếu</code> là hành động tra cứu, không phải một bước.</b> ' +
            'Hệ thống <b>không ghi sổ</b> khi bấm — nên không có timer, không có history, không chặn bước sau.</div>' +
            '<div class="note">Phiếu 1 tờ đơn giản: <b>MO Code nổi bật</b> + tên con hàng + số lượng + ' +
            'TG yêu cầu Step4 + QR. Không cần ký nhận.</div>' +
            '<div class="note warn"><b>Còn treo — §10 #40.</b> Bỏ in ở Kho thì <b>mã QR dán lên hàng đến từ đâu</b>? ' +
            'Tem do ERP in sẵn thì không sao; nếu không thì vẫn phải có chỗ in, chỉ là không phải ở bước này.</div>') +
          '</div></div>';
      }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     1 · SETUP MÁY (§4)
     ═══════════════════════════════════════════════════════════ */
  const SETUP = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        return scanPage({
          dept: 'setup',
          queue: () => M.MOS.filter(m => m.step === 0 && m.accepted),
          qTitle: 'Hàng đợi Setup — chỉ lệnh đã HANDOVER',
          notes: '<div class="note"><b>Chặn cứng:</b> MO chưa được Kho bàn giao thì không nằm ở đây, và quét vào ' +
            'cũng bị từ chối kèm lý do <i>"chưa bàn giao từ Kho"</i> [9A].</div>' +
            '<div class="note"><b>Một lần nhận là một transaction (§9):</b> auto-complete step trước → ' +
            'ghi <code>acceptedAt</code> → cập nhật <code>currentStep</code> → ghi history. Không cho nhảy step.</div>'
        });
      }
    },
    {
      id: 'working', nm: 'Đang setup', sub: 'Không có nút Complete',
      render() {
        return dangO(1, {
          title: 'Đang ở bước 1 · Setup máy',
          act: () => '<span class="dim" style="font-size:12px">chờ QC quét cùng mã</span>'
        }) +
          '<div class="note ok"><b>Setup làm xong KHÔNG bấm Complete.</b> ' +
          'QC quét cùng mã thì Step1 tự đóng, <code>completedAt = QC.acceptedAt</code>. ' +
          'History ghi <code>STEP1_AUTO_COMPLETE</code> kèm <code>triggeredBy</code>.</div>' +
          '<div class="note"><b>Quy tắc chung step 1→3:</b> không có nút Complete riêng — ' +
          '<b>Step N đóng khi Step N+1 nhận</b>. Chỉ Step4 và Step5 có nút riêng, vì hai bước đó cần đo timer song song.</div>';
      }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     2 · QC (§5)
     ═══════════════════════════════════════════════════════════ */
  const QC = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        return scanPage({
          dept: 'qc', queue: () => at(1), qTitle: 'Hàng đợi QC',
          notes: '<div class="note">Quét ở đây vừa <b>nhận cho QC</b> vừa <b>đóng Step1</b> của Setup — ' +
            'một thao tác, hai bút toán.</div>' +
            '<div class="note warn"><b>Quét chỉ thay được thao tác NHẬN (§1b.3).</b> ' +
            'QC vẫn phải chọn PASS/FAIL ở bước sau. Sản xuất vẫn phải nhập SL đạt/hỏng. ' +
            'Đóng thùng vẫn phải nhập SL.</div>'
        });
      }
    },
    {
      id: 'decide', nm: 'PASS / FAIL', sub: 'FAIL bắt buộc ghi lý do',
      render() {
        const mo = at(2)[0];
        if (!mo) return dangO(2, { title: 'Đang ở bước 2 · QC' });
        return dangO(2, {
          title: 'Đang ở bước 2 · QC',
          act: () => '<button class="btn sm primary">Ra kết quả QC</button>'
        }) +
          '<div class="note">QC Accept làm <b>Step1 auto-complete</b>. Bản thân Step2 chỉ đóng khi ' +
          '<b>Bàn team leader</b> Accept. FAIL bắt buộc nhập lý do, ghi <code>QC_FAIL</code> và quay về Kho [§23A].</div>' +
          '<div class="cols c2" style="margin-top:16px"><div>' +
          panel('Kiểm ' + mo.code + ' · ' + mo.sp, 'đang kiểm ' + mo.elapsed,
            '<div class="btnrow" style="margin-bottom:14px">' +
            '<button class="btn primary" style="flex:1;padding:13px">✓ PASS — sang Bàn team leader</button></div>' +
            '<div class="note">PASS thì MO vào hàng đợi Bàn team leader. Không cần ghi gì thêm.</div>' +
            '<hr style="border:0;border-top:1px solid var(--line);margin:18px 0">' +
            '<div class="grid-f" style="grid-template-columns:1fr">' +
            '<div class="field"><label>Lý do FAIL <span class="req">*</span></label>' +
            '<select>' + M.QC_REASONS.map(r => '<option>' + r + '</option>').join('') + '</select>' +
            '<span class="hint">Không chọn lý do thì nút FAIL bị chặn.</span></div>' +
            '<div class="field"><label>Mô tả thêm</label><textarea rows="2" placeholder="Ghi cụ thể để Setup biết chỉnh gì"></textarea></div>' +
            '</div><div class="btnrow" style="margin-top:12px">' +
            '<button class="btn danger" style="flex:1;padding:13px">✕ FAIL — trả về Kho, chạy vòng mới</button></div>') +
          '</div><div>' +
          panel('Vì sao FAIL về KHO, không về Bàn team leader', 'quyết định thiết kế',
            '<div class="note bad"><b>FAIL nghĩa là setup sai.</b> Cho về Bàn team leader thì MO ' +
            '<b>nhảy qua luôn Setup và QC</b> — hàng lỗi setup đi thẳng vào chuyền mà không ai sửa máy.</div>' +
            '<div class="note"><b>Hai đường quay lại, khác nhau ở nguyên nhân:</b><br>' +
            '· <b>Thiếu SL / line dừng quá lâu</b> → về <b>Bàn team leader</b>. Máy setup đúng, hàng đã qua QC — chỉ thiếu số.<br>' +
            '· <b>QC FAIL</b> → về <b>Kho</b>. Phải làm lại từ gốc: Setup chỉnh máy, QC kiểm lại.</div>' +
            '<div class="note"><b>Kết quả QC gắn theo vòng.</b> Sang vòng mới, kết quả cũ cất vào ' +
            '<code>qcHistory</code> rồi xoá — vòng 2 không mang theo chữ FAIL của vòng 1.</div>') +
          '</div></div>';
      }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     3 · BÀN TEAM LEADER (§6)
     ═══════════════════════════════════════════════════════════ */
  const WAITING = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        return scanPage({
          dept: 'waiting',
          queue: () => at(2).concat(M.MOS.filter(m => m.step === 3)),
          qTitle: 'Hàng đợi Bàn team leader',
          notes: '<div class="note"><b>Đây cũng là nơi MO thiếu SL quay về.</b> Máy đã setup đúng, hàng đã qua QC, ' +
            'chỉ là chưa làm đủ số — nên không in lại phiếu, không setup lại, không QC lại.</div>' +
            '<div class="note ok">Vòng mới <b>mở sẵn bước Bàn team leader</b>, MO nằm luôn ở hàng đợi Sản xuất ' +
            'chờ Line Leader quét. <code>M068820</code> vòng 2 đi đường này.</div>' +
            '<div class="note">Giống Setup và QC: <b>không có nút Complete</b>. Bước này đóng lại đúng lúc ' +
            'Sản xuất quét nhận MO để thêm line.</div>'
        });
      }
    },
    {
      id: 'dispatch', nm: 'Chờ vào chuyền', sub: 'Và toàn quyền Step 4',
      render() {
        return dangO(3, {
          title: 'Đang ở bước 3 · Bàn team leader — chờ vào chuyền',
          act: () => '<button class="btn sm primary" data-go="prod/pickline">Gán line →</button>'
        }) +
          '<div class="note ok"><b>Bàn team leader là ngoại lệ DUY NHẤT — có FULL quyền trên Step 4</b>, kể cả Đóng thùng. ' +
          'Gán chuyền, cho chạy, bấm dừng, chốt sổ SX và đóng thùng đều làm được, y như người Sản xuất.</div>' +
          '<div class="note"><b>Lý do:</b> Bàn team leader đứng ngay trước chuyền, thực tế hai tổ này làm việc lẫn nhau. ' +
          'Bắt gọi người Sản xuất sang bấm hộ chỉ tạo thêm một bước thủ tục không ai theo.</div>' +
          '<div class="note warn">Nhìn sidebar: mục <b>Step 4 · Sản xuất</b> của vai này <b>không có nhãn "chỉ xem"</b> — ' +
          'khác hẳn khi đăng nhập bằng vai QC hay Kho.</div>';
      }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     4 · SẢN XUẤT (§7, §7b)
     ═══════════════════════════════════════════════════════════ */
  const PROD = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        return scanPage({
          dept: 'prod', queue: () => M.MOS.filter(m => m.step === 3), qTitle: 'Hàng đợi Sản xuất',
          notes: '<div class="note">MO vòng 2 trở đi từ Bàn team leader xuống thẳng đây — ' +
            '<b>không qua Kho / Setup / QC</b>.</div>' +
            '<div class="note"><b>Nhận xong chưa phải là chạy.</b> Quét ở đây chỉ nhận MO vào Step4; line chưa gán, ' +
            'timer chuyền chưa chạy. Phải sang bước <b>Chọn line</b> rồi <code>Thêm line vào bảng</code> thì ' +
            '<code>TG chờ</code> mới bắt đầu [11B].</div>'
        });
      }
    },
    {
      id: 'pickline', nm: 'Chọn line', sub: '14 line, tick 1..n',
      render() {
        const chips = M.LINES.map(l => {
          const cls = l.st === 'on' ? 'on' : l.st === 'busy' ? 'busy' : l.st === 'stop' ? 'stop' : '';
          const lb = l.st === 'free' ? 'trống' : l.st === 'stop' ? 'đang dừng' : l.by;
          return '<button class="lchip ' + cls + '">L' + String(l.n).padStart(2, '0') + '<em>' + lb + '</em></button>';
        }).join('');
        return '<div class="cols c2"><div>' +
          panel('Chọn line cho M068825 · Lò xo F', '§7.1 · 14 line',
            chips +
            '<div class="btnrow" style="margin-top:14px"><button class="btn primary">Thêm line vào bảng (2 line)</button>' +
            '<span class="muted" style="font-size:12px">Đã chọn L03, L04</span></div>' +
            '<div class="note"><b>1 MO gộp 1 dòng</b>, cột <code>Line</code> hiển thị <code>L03, L04</code> — ' +
            '<b>không chia SL theo line</b>. 1 line chạy nhiều MO cùng lúc cũng không chặn [14B].</div>') +
          '</div><div>' +
          panel('Mốc SL đóng dấu lúc thêm line', '§7.3',
            '<div class="note acc" style="background:var(--accent-tint);border-color:transparent;color:var(--accent)">' +
            '<b>TG yêu cầu của vòng = requiredProductionTime × SL vòng / SL MO.</b><br>' +
            'MO 10.000 yêu cầu 3 giờ. Vòng 1 làm đủ 10.000 → hạn <b>180 phút</b>. ' +
            'Vòng 2 chỉ còn 1.000 → hạn <b>18 phút</b>.</div>' +
            '<div class="note">Mốc này <b>đóng dấu vào run ngay lúc thêm line</b>, nên MO đã xong vẫn giữ ' +
            'đúng hạn mức của vòng đó. Không so với <code>quantity</code> — nếu không thì vòng nào cũng Đạt.</div>' +
            '<div class="note">Line chỉ chọn được khi <b>vòng hiện tại</b> chưa có line đó. Line của vòng trước không chặn vòng sau.</div>') +
          '</div></div>';
      }
    },
    {
      id: 'board', nm: 'Bảng đang chạy', sub: 'Chờ xử lý ⇄ Đang lắp ráp',
      render() { return runBoard(true) + haiNhanh(); }
    },
    {
      id: 'hourly', nm: 'Sản lượng giờ', sub: 'Ba số bắt buộc',
      render() {
        /* Nhật ký append-only của cả trạm, đủ 11 cột theo schema §7.2b.
           Dòng tổng chỉ cộng trong phạm vi MO đang chạy — cộng ngang
           nhiều MO thì con số không có nghĩa gì. */
        const cur = M.HOURLY.filter(h => h.mo === 'M068820');
        const sum = cur.reduce((a, h) => a + h.qty, 0);
        const sumT = cur.reduce((a, h) => a + h.target, 0);
        const rows = M.HOURLY.map(h =>
          '<tr' + (h.mo === 'M068820' ? ' class="hl"' : '') + '>' +
          '<td class="mono">' + h.day + '</td><td class="mono">' + h.slot + '</td>' +
          '<td class="mono"><b>' + h.mo + '</b></td><td class="num">' + h.r + '</td>' +
          '<td class="num">' + h.people + '</td><td class="num">' + nf(h.target) + '</td>' +
          '<td class="num"><b>' + nf(h.qty) + '</b></td>' +
          '<td class="num"><span class="bdg ' + (h.qty >= h.target ? 'ok' : 'warn') + '">' +
          Math.round(h.qty / h.target * 100) + '%</span></td>' +
          '<td class="num">' + (h.qty / h.people).toFixed(1) + '</td>' +
          '<td class="dim">' + (h.note || '—') + '</td>' +
          '<td class="mono dim">' + h.at + '</td><td class="dim">' + h.by + '</td></tr>').join('');
        return '<div class="note ok"><b>Nhánh CHUYỀN · việc lặp mỗi khung giờ.</b> ' +
          'Mở được vì <code>L01, L02</code> đã vào <code>Đang lắp ráp</code> lúc <b>09:24</b>. ' +
          'Đây không phải một bước làm một lần rồi qua bước sau — mỗi giờ ghi một dòng, ' +
          'chạy song song với nhánh Đóng thùng suốt ca.</div>' +
          panel('Ghi sản lượng khung giờ', 'chỉ hiện khi có MO Đang lắp ráp',
          '<div class="grid-f">' +
          fld('MO', '<select><option>M068820 · Vỏ máy bơm A</option><option>M068827 · Ốc vít H</option></select>') +
          fld('Khung giờ', '<select>' + M.SLOTS.slice(0, 12).map((s, i) => '<option' + (i === 8 ? ' selected' : '') + '>' + s + '</option>').join('') + '</select>') +
          fld('Số người <span class="req">*</span>', '<input type="number" value="12">', 'mẫu số của Năng suất') +
          fld('Sản lượng yêu cầu <span class="req">*</span>', '<input type="number" value="600">', 'mẫu số của Đạt %') +
          fld('Sản lượng thực tế <span class="req">*</span>', '<input type="number" value="583">', 'cộng dồn, đối soát SX đạt') +
          fld('Ghi chú', '<input placeholder="Kẹt liệu 8 phút">') +
          '</div><div class="btnrow" style="margin-top:12px"><button class="btn primary">Ghi</button>' +
          '<span class="muted" style="font-size:12px">Đạt % và Năng suất do hệ thống tự tính — không có ô nhập.</span></div>') +
          panel('Nhật ký sản lượng theo giờ', M.HOURLY.length + ' bản ghi · append-only',
            tbl([{ t: 'Ngày' }, { t: 'Khung giờ' }, { t: 'MO' }, { t: 'Vòng', num: 1 },
            { t: 'Số người', num: 1 }, { t: 'SL yêu cầu', num: 1 }, { t: 'SL thực tế', num: 1 },
            { t: 'Đạt %', num: 1 }, { t: 'Năng suất', num: 1 }, { t: 'Ghi chú' },
            { t: 'Ghi lúc' }, { t: 'Người ghi' }], rows), true) +
          '<div class="note"><b>Đối soát M068820 · vòng 2:</b> Σ giờ <b class="mono">' + nf(sum) + '</b> / ' +
          'Σ yêu cầu <b class="mono">' + nf(sumT) + '</b> · mục tiêu vòng <b class="mono">2.000</b> — ' +
          'chưa chốt sổ SX nên chưa so được với <code>SX đạt</code>. ' +
          'Σ giờ <b>&lt;</b> SX đạt là ghi sót giờ, bình thường; Σ giờ <b>&gt;</b> SX đạt mới là bất thường, báo đỏ.</div>' +
          '<div class="note warn"><b>Vì sao phải có cột Ngày.</b> Hai dòng <code>M068827</code> cùng khung ' +
          '<code>02:00-03:00</code> nhưng khác ngày — MO chạy qua đêm, cả hai đều hợp lệ. ' +
          'Khoá chặn trùng là <b>ngày + khung giờ</b>, không phải chỉ khung giờ.</div>' +
          '<div class="note"><b>Vì sao phải đủ ba số.</b> Một mình con số làm ra được không trả lời được câu duy nhất ' +
          'người quản lý cần hỏi: <i>giờ vừa rồi chạy tốt hay không</i>. 500 cái với 8 người là khá; 500 cái với 20 người là có vấn đề. ' +
          'Định mức 400 thì 500 là vượt; định mức 700 thì 500 là hụt.</div>' +
          '<div class="note warn"><b>Chặn vượt:</b> tổng SL thực tế không vượt mục tiêu vòng. ' +
          'Nhưng vượt <code>SL yêu cầu</code> của <b>một khung</b> thì không chặn — <code>Đạt 117%</code> là tin tốt, không phải lỗi. ' +
          'Chỉ mục tiêu cả vòng mới là trần cứng. Chặn trùng theo <b>ngày + khung giờ</b>, nên MO chạy qua đêm vẫn ghi được cùng khung hôm sau.</div>';
      }
    },
    {
      id: 'close', nm: 'Chốt sổ SX', sub: 'Ba ô SL phải cộng đúng',
      render() {
        return '<div class="note ok"><b>Nhánh CHUYỀN · bút toán cuối.</b> ' +
          'Chốt sổ SX <b>không đụng tới nhánh Đóng thùng</b> — đóng thùng đã chạy từ 09:31 và vẫn đang chạy. ' +
          'Chốt xong mới <b>mở khoá</b> cho <code>Kết thúc đóng thùng</code> bên nhánh kia.</div>' +
          '<div class="cols c2"><div>' +
          panel('Hoàn thành Step4 — M068820 · vòng 2', 'mục tiêu vòng 2.000',
            '<div class="note">Đối soát: <b>cần 2.000</b> · <b>Σ giờ 1.983</b></div>' +
            '<div class="grid-f" style="margin-top:14px;grid-template-columns:repeat(3,1fr)">' +
            fld('SL đạt <span class="req">*</span>', '<input type="number" id="sx-ok" value="1983">') +
            fld('SL hỏng <span class="req">*</span>', '<input type="number" id="sx-ng" value="12">') +
            fld('SL thiếu <span class="req">*</span>', '<input type="number" id="sx-short" value="5">') +
            '</div>' +
            '<div id="sx-sum" class="note ok" style="margin-top:12px"></div>' +
            '<div class="grid-f" style="margin-top:12px;grid-template-columns:1fr 1fr">' +
            fld('Lý do hỏng <span class="req">*</span>', '<input value="Lỗi ép nhựa">', 'bắt buộc khi SL hỏng > 0') +
            fld('Lý do thiếu <span class="req">*</span>', '<input value="Hết ca">', 'bắt buộc khi SL thiếu > 0') +
            '</div>' +
            '<div class="btnrow" style="margin-top:14px"><button class="btn primary">Xác nhận chốt sổ</button>' +
            '<button class="btn ghost">Huỷ</button></div>') +
          '</div><div>' +
          panel('Ba ô SL là chốt đối soát của cả bước', '§7.5',
            '<div class="note"><b>Mỗi PCS giao xuống chuyền phải rơi vào đúng một trong ba nhóm:</b> ' +
            'làm ra đạt · làm ra nhưng hỏng · không làm ra được. Tổng lệch nghĩa là có hàng không ai khai — ' +
            'hệ thống <b>chặn, không cho chốt sổ</b>.</div>' +
            '<div class="note">Thử sửa số trong ba ô bên trái — dòng tổng đổi ngay sang ' +
            '<code>đang dư</code> / <code>đang hụt</code>. <b>Không bắt người vận hành bấm Xác nhận rồi mới biết mình gõ lệch.</b></div>' +
            '<div class="note warn"><b>Hỏng và thiếu là hai chuyện khác nhau, phải hỏi riêng.</b> ' +
            'Hỏng 500 vì lỗi khuôn; thiếu 1.000 vì chờ bù liệu. Gộp một ô thì một trong hai mất hẳn thông tin — ' +
            'mà <b>làm thiếu không hỏng cái nào là chuyện rất thường</b> (hết liệu, đổi ca, máy chậm).</div>' +
            '<div class="note bad"><b>SL hỏng ghi ở đây, không ghi ở Đóng thùng.</b> Chuyền mới là chỗ phát hiện hàng lỗi. ' +
            'Hàng xuống tới đóng thùng là hàng đã đạt.</div>' +
            '<div class="note"><b>Mỗi vòng chỉ chốt sổ một lần.</b> Gọi lại bị chặn (<code>SX vòng 2 đã chốt sổ rồi</code>) — ' +
            'nếu không, lần chốt thứ hai ghi đè SL đã khai mà không để lại dấu vết.</div>') +
          '</div></div>' +
          '<div class="note">[16] Các line của 1 MO <b>hoàn thành đồng bộ</b>. Chặn khi còn line chưa vào ' +
          '<code>Đang lắp ráp</code> hoặc còn line đang dừng — báo rõ line nào. [21A] KPI tổng MO lấy <b>line chạy lâu nhất</b>.</div>';
      }
    },
    {
      id: 'packing', nm: 'Đóng thùng', sub: 'Song song trong Step4',
      render() {
        /* Nhật ký append-only đủ 9 cột theo schema §7b.2 */
        const cur = M.PACK_HOURLY.filter(p => p.mo === 'M068820');
        const boxes = cur.reduce((a, p) => a + p.boxes, 0);
        const rows = M.PACK_HOURLY.map(p =>
          '<tr' + (p.mo === 'M068820' ? ' class="hl"' : '') + '>' +
          '<td class="mono">' + p.day + '</td><td class="mono">' + p.slot + '</td>' +
          '<td class="mono"><b>' + p.mo + '</b></td><td class="num">' + p.r + '</td>' +
          '<td class="num"><b>' + p.boxes + '</b></td><td class="num">' + nf(p.pcsBox) + '</td>' +
          '<td class="num">' + nf(p.boxes * p.pcsBox) + '</td>' +
          '<td class="dim">' + (p.note || '—') + '</td>' +
          '<td class="mono dim">' + p.at + '</td><td class="dim">' + p.by + '</td></tr>').join('');
        return '<div class="note ok"><b>Nhánh ĐÓNG THÙNG · mở song song, không chờ Chốt sổ SX.</b> ' +
          'Điều kiện mở là <b>ít nhất 1 line đã <code>Đang lắp ráp</code></b> — L01 vào lúc 09:24, ' +
          'nên nút <code>Bắt đầu</code> sáng lên từ 09:24 và đã bấm lúc <b>09:31</b>. ' +
          'Hàng ra khỏi chuyền là đóng luôn.</div>' +
          '<div class="cols c2"><div>' +
          panel('Tiến trình đóng thùng — M068820', 'timer riêng',
            '<div class="tiles">' +
            tile('Bắt đầu lúc', '09:31', 'PACK_START', 'acc') +
            tile('Đã đóng', boxes * 200, boxes + ' thùng · 200 pcs/thùng', 'ok') +
            tile('Timer đóng thùng', '2h18', 'đang chạy', '') +
            '</div>' +
            '<div class="btnrow" style="margin-top:14px">' +
            '<button class="btn" disabled>Bắt đầu đóng thùng</button>' +
            '<button class="btn primary" data-go="prod/packclose">Kết thúc đóng thùng →</button></div>' +
            '<div class="note"><b>Bắt đầu</b> chỉ hiện nút khi ít nhất 1 line đã <code>Đang lắp ráp</code>. ' +
            'Không auto-close SX.</div>') +
          panel('Đóng thùng theo giờ', '§7b.2',
            '<div class="grid-f">' +
            fld('MO', '<select><option>M068820 · quy cách 200</option></select>') +
            fld('Khung giờ', '<select>' + M.SLOTS.slice(0, 12).map((s, i) => '<option' + (i === 8 ? ' selected' : '') + '>' + s + '</option>').join('') + '</select>') +
            fld('Số thùng ĐẦY <span class="req">*</span>', '<input type="number" value="2">') +
            fld('Ghi chú', '<input placeholder="Thiếu thùng carton">') +
            '</div><div class="btnrow" style="margin-top:12px"><button class="btn primary">Ghi</button></div>') +
          '</div><div>' +
          panel('Nhật ký đóng thùng theo giờ', M.PACK_HOURLY.length + ' bản ghi · append-only',
            tbl([{ t: 'Ngày' }, { t: 'Khung giờ' }, { t: 'MO' }, { t: 'Vòng', num: 1 },
            { t: 'Số thùng', num: 1 }, { t: 'Quy cách', num: 1 }, { t: '= PCS', num: 1 },
            { t: 'Ghi chú' }, { t: 'Ghi lúc' }, { t: 'Người ghi' }], rows), true) +
          '<div class="note"><b>M068820 · vòng 2:</b> ' + boxes + ' thùng × 200 = <b class="mono">' +
          nf(boxes * 200) + ' pcs</b>. Không cộng ngang các MO: dòng <code>M068830</code> quy cách ' +
          '<b>150</b>, nên "6 thùng" của nó ra 900 pcs chứ không phải 1.200. ' +
          '<b>Đó là lý do <code>pcsPerBox</code> phải lưu theo từng bản ghi</b>, không đọc từ MO lúc hiển thị — ' +
          'quy cách đổi sau này thì số cũ vẫn phải giữ nguyên.</div>' +
          '<div class="note"><b>Đóng thùng thuộc phòng Sản xuất</b>, không phải phòng thứ bảy. ' +
          'Nó chạy song song bên trong Step 4 chứ không phải một step riêng, nên quyền của nó đi theo Sản xuất.</div>' +
          '<div class="note warn">Panel này <b>chỉ hiện khi MO đang đóng thùng và đã khai <code>Quy cách</code></b>. ' +
          'MO <code>M068826</code> có <code>pcsPerBox = 0</code> → không đóng thùng, panel ẩn hẳn.</div>' +
          '<div class="note">MO <b>ở lại Step4</b> cho đến khi có <code>packing.completedAt</code> — ' +
          'chưa đóng thùng xong thì Kho nhập không thấy.</div>' +
          '</div></div>';
      }
    },
    {
      id: 'packclose', nm: 'Kết thúc đóng thùng', sub: 'Phải sau khi chốt sổ SX',
      render() {
        return '<div class="note warn"><b>Nhánh ĐÓNG THÙNG · điểm giao nhau duy nhất của hai nhánh.</b> ' +
          'Đây là chỗ <b>duy nhất</b> trong Step 4 mà một nhánh phải chờ nhánh kia: chỉ mở khi ' +
          '<code>Chốt sổ SX</code> đã xong. <code>M068820</code> chưa chốt sổ nên nút này còn bị chặn; ' +
          'form dưới đây dùng <code>M068830</code> — MO đã chốt sổ SX lúc 12:02.</div>' +
          '<div class="cols c2"><div>' +
          panel('Kết thúc đóng thùng — M068830 · Đế cao su J', 'SX đã chốt sổ',
            '<div class="note">Đối soát: <b>SX đạt 5.800</b> · <b>Σ giờ 5.780</b></div>' +
            '<div class="grid-f" style="margin-top:14px;grid-template-columns:1fr">' +
            fld('SL đã đóng thùng <span class="req">*</span>', '<input type="number" id="pk-qty" value="5800">', 'mặc định bằng SL đạt của SX') +
            '</div>' +
            '<div id="pk-sum" class="note ok" style="margin-top:12px"></div>' +
            '<div class="grid-f" style="margin-top:12px;grid-template-columns:1fr">' +
            fld('Lý do / ghi chú <span class="req">*</span>', '<input value="Đóng đủ hàng đạt">', 'luôn bắt buộc, kể cả khi đóng đủ') +
            '</div>' +
            '<div class="btnrow" style="margin-top:14px"><button class="btn primary">Xác nhận kết thúc</button></div>') +
          '</div><div>' +
          panel('Ràng buộc và đuôi đóng thùng', '§7b',
            '<div class="note"><b>Không còn ô <code>SL hỏng</code></b> — đã chuyển hẳn sang bước Sản xuất.</div>' +
            '<div class="note warn"><b>Kết thúc phải sau khi Hoàn thành SX.</b> Cái sản phẩm cuối ra khỏi chuyền ' +
            'thì mới đóng xong được — ràng buộc này đúng thực tế nên giữ.</div>' +
            '<div class="note"><b>Đuôi đóng thùng = <code>packing.completedAt − steps[4].completedAt</code>.</b> ' +
            'Timer đóng thùng tổng bao trùm cả phần đuôi của SX nên không đo được năng suất đóng thùng riêng — ' +
            'thêm cột đuôi để biết sau khi line dừng còn mất bao lâu.</div>' +
            '<div class="note bad"><b>Cảnh báo khi SX đạt ≠ SL đóng thùng</b> được ghi vào ' +
            '<code>PACK_COMPLETE</code> — lộ ra hàng đạt mà chưa đóng hết (hết thùng, hết ca).</div>') +
          '</div></div>';
      }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     5 · KHO NHẬP (§8)
     ═══════════════════════════════════════════════════════════ */
  const WH_IN = [
    {
      id: 'scan', nm: 'Quét nhận', sub: 'Hàng đợi + nhận tại trạm',
      render() {
        return scanPage({
          dept: 'wh_in',
          queue: () => M.MOS.filter(m => m.runSt === 'DONE'),
          qTitle: 'Hàng đợi Kho nhập',
          /* Bảng riêng thay cho danh sách chung: ở đây người kho cần thấy
             SL đã đóng thùng trước khi mở thùng ra đếm. */
          qBody: q => tbl(
            [{ t: 'MO' }, { t: 'Tên con hàng' }, { t: 'SL kế hoạch', num: 1 },
            { t: 'Đã đóng thùng', num: 1 }, { t: 'SX đạt', num: 1 }, { t: 'Ghi chú' }],
            q.map(m => '<tr data-pick="' + m.code + '" style="cursor:pointer">' +
              '<td class="mono"><b>' + m.code + '</b></td><td>' + m.sp + '</td>' +
              '<td class="num">' + nf(m.qty) + '</td><td class="num"><b>' + nf(m.packed) + '</b></td>' +
              '<td class="num">' + nf(m.sxOk) + '</td><td>' + badges(m) + '</td></tr>').join('') ||
            '<tr><td colspan="6">' + empty('🏬', 'Chưa có lô nào về kho', 'Chờ Sản xuất kết thúc đóng thùng.') + '</td></tr>'),
          notes: '<div class="note">Hàng đợi hiển thị <b>SL đã đóng thùng của vòng này</b> để đối soát — ' +
            'người kho biết trước sắp đếm bao nhiêu trước khi mở thùng.</div>' +
            '<div class="note warn"><b>Kho nhập ≠ Kho xuất.</b> Hai toà nhà, hai tổ người, hai người quản lý. ' +
            'Kho xuất giữ vật tư và cho hàng <b>ra</b>; kho nhập giữ thành phẩm và nhận hàng <b>vào</b>. ' +
            'Gộp chung một vai thì người giao vật tư tự nhận luôn thành phẩm của chính lô mình giao — ' +
            'mất hẳn lớp đối soát giữa đầu vào và đầu ra.</div>' +
            '<div class="note"><b>Bước cuối — giữ nút Hoàn thành (§8).</b> Step5 là một trong hai bước có nút riêng ' +
            '(cùng Step4). Các bước 1→3 đóng lại tự động khi bước sau nhận, nhưng Step5 không có bước sau — ' +
            'phải có người xác nhận đã đếm xong.</div>'
        });
      }
    },
    {
      id: 'finish', nm: 'Hoàn thành', sub: 'Đủ SL hay trả về vòng mới',
      render() {
        const mo = at(5)[0];
        if (!mo) return dangO(5, { title: 'Đang ở bước 5 · Kho nhập' });
        const tong = mo.done + mo.packed;             // §8 — kiểm tra cộng dồn
        const du = tong >= mo.qty;
        return dangO(5, {
          title: 'Đang ở bước 5 · Kho nhập',
          act: () => '<button class="btn sm primary">Đếm và chốt</button>'
        }) +
          '<div class="cols c2" style="margin-top:16px"><div>' +
          panel('Chốt ' + mo.code + ' · ' + mo.sp, 'kiểm tra cộng dồn',
            '<div class="tiles" style="margin-bottom:14px">' +
            tile('SL kế hoạch', mo.qty, 'quantity', '') +
            tile('qtyDone trước', mo.done, 'các vòng trước', '') +
            tile('Đóng thùng vòng này', mo.packed, 'packing', 'acc') +
            '</div>' +
            '<div class="note ' + (du ? 'ok' : 'bad') + '"><b>tổng = ' + nf(mo.done) + ' + ' + nf(mo.packed) +
            ' = ' + nf(tong) + (du ? ' ≥ ' : ' &lt; ') + nf(mo.qty) + '</b> → ' +
            (du ? '<b>COMPLETED</b>, chốt sổ vòng cuối vào <code>packingHistory</code>.'
              : 'CHƯA HOÀN THÀNH, tự động về <b>Bàn team leader</b> vòng mới.') + '</div>' +
            '<div class="btnrow" style="margin-top:14px"><button class="btn primary">Hoàn thành</button></div>' +
            (du ? '' : '<div class="note">Sau khi bấm: <code>qtyDone = ' + nf(mo.packed) + '</code> · ' +
              '<code>qtyNgTotal = ' + nf(mo.sxNg) + '</code> · <code>qtyRemain = ' + nf(mo.qty - tong) + '</code>. ' +
              'UI hiện <code>Đã xong ' + nf(mo.packed) + ' — Còn ' + nf(mo.qty - tong) + '</code> + ' +
              '<code>Trả lại lần 1</code>.</div>')) +
          '</div><div>' +
          panel('Hai ngả của nút Hoàn thành', '§8 · §6b', hai_nga()) +
          '</div></div>' +
          panel('Ví dụ đủ SL — M068819 · Ống dẫn L', 'COMPLETED 09:48',
            '<div class="note ok"><b>tổng = 0 + 9.000 = 9.000 ≥ 9.000</b> → <b>COMPLETED</b>, ' +
            'chốt sổ vòng cuối vào <code>packingHistory</code>. ' +
            '<b>Vòng cuối cũng được ghi sổ</b> — MO xong ngay vòng 1 vẫn có một dòng trong bảng Các vòng.</div>');
      }
    }
  ];

  /* §7b — Hai nhánh của Step 4 đặt cạnh nhau, cùng một mốc gốc, để
     nhìn là thấy chúng chạy chồng thời gian chứ không nối đuôi. */
  function haiNhanh() {
    const mo = M.MOS.find(m => m.code === 'M068820');
    const sxDone = mo.sxOk != null;
    return panel('Hai nhánh của Step 4 — chạy chồng thời gian', mo.code + ' · vòng ' + mo.round,
      '<div class="lane2">' +
      '<div class="ln"><div class="hd"><b>Chuyền · Sản xuất</b>' +
      '<span class="bdg ok"><span class="pulse"></span>Đang lắp ráp</span></div>' +
      '<div class="mt">Mở lúc <b class="mono">' + mo.runStart + '</b> — khi bấm <code>Đang lắp ráp</code> ' +
      'trên line ' + mo.lines + '.</div>' +
      '<div class="mt">TG thực tế <b class="mono">' + mo.actual + '</b> · hạn mức vòng ' +
      '<b class="mono">' + mo.limit + '</b>.</div>' +
      '<div class="mt">Chốt sổ SX: <b>' + (sxDone ? 'đã chốt' : 'chưa') + '</b>.</div></div>' +

      '<div class="ln"><div class="hd"><b>Đóng thùng</b>' +
      '<span class="bdg ok"><span class="pulse"></span>Đang đóng</span></div>' +
      '<div class="mt">Mở lúc <b class="mono">' + mo.packStart + '</b> — <b>7 phút sau</b> khi line vào ' +
      '<code>Đang lắp ráp</code>, <b>không chờ chốt sổ SX</b>.</div>' +
      '<div class="mt">Timer đóng thùng <b class="mono">' + mo.packTimer + '</b> · đã đóng ' +
      '<b class="mono">' + mo.packBoxes + ' thùng</b> = ' + nf(mo.packBoxes * mo.pcsBox) + ' pcs.</div>' +
      '<div class="mt">Kết thúc: <b>bị chặn</b> — chờ Chốt sổ SX.</div></div>' +
      '</div>' +

      '<div class="note"><b>Đây là chỗ dễ đọc nhầm nhất của Step 4.</b> Hai nhánh mở cách nhau 7 phút và ' +
      'chạy chồng nhau suốt ca — <b>không phải đóng thùng xong sản xuất mới bắt đầu</b>. Hàng ra khỏi chuyền ' +
      'là đóng luôn; chốt sổ SX chỉ là bút toán cuối của nhánh chuyền.</div>' +
      '<div class="note warn"><b>Ràng buộc duy nhất giữa hai nhánh:</b> <code>Kết thúc đóng thùng</code> phải sau ' +
      '<code>Chốt sổ SX</code>. Cái sản phẩm cuối ra khỏi chuyền thì mới đóng xong được. ' +
      'Khoảng lệch đó là <b>đuôi đóng thùng</b> = <code>packing.completedAt − steps[4].completedAt</code>.</div>' +
      '<div class="note">Step 4 sang Step 5 khi <b>cả hai nhánh</b> đã kết thúc. ' +
      'Chốt sổ SX xong mà chưa đóng thùng xong thì MO vẫn ở lại Step 4, Kho nhập chưa thấy.</div>');
  }

  function hai_nga() {
    return '<div class="note ok"><b>tổng ≥ quantity → COMPLETED.</b> Chốt sổ vòng cuối, MO đóng hẳn.</div>' +
      '<div class="note warn"><b>tổng &lt; quantity → về BÀN TEAM LEADER, vòng mới.</b> ' +
      'Status <b>vẫn PROCESSING</b> — chỉ <code>round</code> tăng và <code>currentStep</code> về 3.</div>' +
      '<div class="note"><b>Vòng mới dọn sạch để bắt đầu trắng:</b> <code>steps{}</code> snapshot rồi reset rỗng; ' +
      '<code>qc</code> · <code>packing</code> · <code>sx</code> snapshot rồi xoá. ' +
      '<code>runs[]</code>, <code>hourly[]</code> giữ nguyên vì mỗi bản ghi có <code>round</code> riêng nên không lẫn.</div>' +
      '<div class="note bad"><b>Vì sao phải reset <code>steps</code>:</b> <code>steps[5].acceptedAt</code> của vòng cũ ' +
      'sẽ khiến MO <b>không bao giờ vào lại được hàng đợi Nhập kho</b> — đóng thùng xong cũng kẹt.</div>' +
      '<div class="note"><b>SL hỏng không tính là đã xong</b> → phải làm bù ở vòng sau, và được đếm riêng để tính tỷ lệ phế.</div>';
  }

  /* ═══════════════════════════════════════════════════════════
     PLANNER (§2, §9)
     ═══════════════════════════════════════════════════════════ */
  const PLANNER = [
    {
      id: 'dash', nm: 'Tổng quan', sub: 'Toàn xưởng một màn hình',
      render() {
        const busy = M.LINES.filter(l => l.st !== 'free').length;
        const cards = M.DEPTS.filter(d => d.step !== null).map(d => {
          const n = d.step === 0 ? M.MOS.filter(m => m.step === 0).length
            : d.step === 4 ? M.MOS.filter(m => m.step === 4).length
              : at(d.step).length;
          return '<button class="sb-item" data-go="' + d.id + '/queue" style="border:1px solid var(--line);margin-bottom:6px">' +
            '<span class="ic">' + d.ic + '</span><span class="tx">' + d.full + '</span>' +
            '<span class="ct' + (n ? '' : '') + '">' + n + '</span></button>';
        }).join('');
        return '<div class="tiles" style="margin-bottom:16px">' +
          tile('MO đang chạy', M.MOS.filter(m => m.st === 'PROCESSING').length, 'PROCESSING', 'acc') +
          tile('Line đang bận', busy + '/14', '1 line đang dừng', 'warn') +
          tile('Rework', 1, 'QC FAIL trả về Kho', 'bad') +
          tile('Đang ở vòng 2+', M.MOS.filter(m => m.round > 1).length, 'chưa đủ SL', 'warn') +
          tile('Hoàn thành hôm nay', 1, 'COMPLETED', 'ok') +
          '</div>' +
          '<div class="cols c2"><div>' +
          panel('Tồn theo trạm', 'bấm để mở trạm', cards) +
          '</div><div>' +
          panel('Cần chú ý', '3 việc',
            '<div class="note bad"><b>M068827 — L06 đang dừng 1h12.</b> Hỏng khuôn ép, chờ thợ. ' +
            'Dừng quá lâu thì cân nhắc trả về Bàn team leader chạy vòng mới.</div>' +
            '<div class="note warn"><b>M068820 — quá giờ 5 phút 05 giây.</b> Hạn mức vòng 2 là 36 phút (2.000/10.000 × 3 giờ).</div>' +
            '<div class="note"><b>M068826 — Rework vòng 2</b> đang nằm ở hàng đợi Kho xuất, chưa ai nhận.</div>') +
          '</div></div>' +
          '<div class="note"><b>PLANNER full quyền mọi step của mọi phòng ban</b> — xem, quét nhận, nhập sửa. ' +
          'Đây là vai điều độ, phải vào được mọi chỗ khi có sự cố. Sidebar của vai này liệt kê đủ 6 trạm, không có nhãn "chỉ xem".</div>';
      }
    },
    {
      id: 'create', nm: 'Tạo MO', sub: 'Lẻ · hàng loạt · CSV',
      render() {
        return '<div class="cols c2"><div>' +
          panel('Tạo lẻ', '§2.2 · 1C',
            '<div class="grid-f">' +
            fld('Mã MO <span class="req">*</span>', '<input class="mono" value="M068831">', 'M + đúng 6 chữ số') +
            fld('Tên con hàng <span class="req">*</span>', '<input value="Vỏ hộp số M">') +
            fld('Số lượng <span class="req">*</span>', '<input type="number" value="7500">') +
            fld('Đơn vị', '<select><option>PCS</option></select>') +
            fld('Quy cách (pcs/thùng)', '<input type="number" value="250">', '0 = không đóng thùng') +
            fld('TG yêu cầu Step4 <span class="req">*</span>', '<input value="2 giờ 30 phút">', 'chỉ áp dụng cho Step4 [3A]') +
            '</div><div class="btnrow" style="margin-top:12px"><button class="btn primary">Tạo (DRAFT)</button></div>') +
          panel('Tạo hàng loạt', '10–100 MO/lần',
            '<div class="grid-f">' +
            fld('Số bắt đầu <span class="req">*</span>', '<input class="mono" value="067690">') +
            fld('Số lượng MO <span class="req">*</span>', '<input type="number" value="25">') +
            fld('Tên con hàng', '<input value="Chốt định vị N">') +
            fld('SL mỗi MO', '<input type="number" value="2000">') +
            '</div>' +
            '<div class="note">Mã chạy liên tục: <code>M067690</code>, <code>M067691</code>, … ' +
            'Chạy trong <b>transaction</b> — trùng 1 mã thì <b>không tạo dòng nào</b>.</div>' +
            '<div class="btnrow" style="margin-top:12px"><button class="btn primary">Tạo 25 MO</button></div>') +
          '</div><div>' +
          panel('Import CSV', '§2.2 · 2C',
            '<div class="field"><label>4 cột: Mã, Tên con hàng, Số lượng, TG yêu cầu Step4</label>' +
            '<textarea rows="6" class="mono" style="font-size:12px">M067690,Chốt định vị N,2000,45p\nM067691,Chốt định vị N,2000,45p\nM06769X,Sai định dạng,2000,45p</textarea></div>' +
            '<div class="note bad"><b>Dòng 3 bị chặn ngay:</b> <code>M06769X</code> sai định dạng. ' +
            'Mã sai thì chặn cả khi nhập tay lẫn khi import — không import một nửa rồi báo lỗi sau.</div>' +
            '<div class="btnrow" style="margin-top:12px"><button class="btn primary">Import</button></div>') +
          panel('Khoá cứng sau Submit', '§2.2 · 4A',
            '<div class="note warn">Sau Submit, <b>khoá cứng</b> <code>moCode</code> · <code>product</code> · ' +
            '<code>quantity</code> · <code>requiredProductionTime</code> · <code>pcsPerBox</code>. ' +
            'Nhập sai thì <code>CANCELLED</code> kèm lý do + tạo MO mới. <b>Không hard delete.</b></div>' +
            '<div class="note"><b>CẦN CHỐT (§10):</b> số chạy 6 chữ số do <b>hệ thống tự cấp</b> hay lấy từ <b>ERP bên ngoài</b>? ' +
            'Nếu lấy từ ERP thì không được tự sinh — chỉ nhập tay hoặc import, và phần <b>tạo hàng loạt phải bỏ</b>.</div>') +
          '</div></div>';
      }
    },
    {
      id: 'book', nm: 'Sổ lệnh', sub: 'Submit · Cancel',
      render() {
        const rows = M.MOS.map(m => {
          const stt = m.st === 'DRAFT' ? '<span class="bdg">DRAFT</span>'
            : m.st === 'SUBMITTED' ? '<span class="bdg acc">SUBMITTED</span>'
              : m.st === 'COMPLETED' ? '<span class="bdg ok">COMPLETED</span>'
                : '<span class="bdg warn">PROCESSING</span>';
          const where = m.step === null ? '—' : m.step + ' · ' + (M.DEPTS.find(d => d.step === m.step) || {}).nm;
          return '<tr><td class="mono"><b>' + m.code + '</b></td><td>' + m.sp + '</td>' +
            '<td class="num">' + nf(m.qty) + '</td><td class="num">' + (m.pcsBox || '—') + '</td>' +
            '<td class="mono">' + m.req + '</td><td>' + stt + '</td><td>' + where + '</td>' +
            '<td class="num">' + m.round + '</td><td>' + badges(m) + '</td>' +
            '<td class="right">' + (m.st === 'DRAFT'
              ? '<button class="btn sm primary">Submit</button>'
              : m.st === 'COMPLETED' ? '<button class="btn sm" data-go="planner/trace">Truy cứu</button>'
                : '<button class="btn sm danger">Huỷ</button>') + '</td></tr>';
        }).join('');
        return panel('Sổ lệnh', M.MOS.length + ' MO',
          tbl([{ t: 'MO' }, { t: 'Tên con hàng' }, { t: 'SL', num: 1 }, { t: 'Quy cách', num: 1 }, { t: 'TG yêu cầu' },
          { t: 'Status' }, { t: 'Đang ở' }, { t: 'Vòng', num: 1 }, { t: 'Ghi chú' }, { t: '' }], rows), true) +
          '<div class="note"><b><code>status</code> và <code>currentStep</code> tách riêng.</b> ' +
          'MO chưa hoàn thành <b>không đổi status</b> — vẫn <code>PROCESSING</code>, chỉ <code>round</code> tăng và ' +
          '<code>currentStep</code> về 3 hoặc 0 tuỳ nguyên nhân.</div>';
      }
    },
    { id: 'board', nm: 'Bảng đang chạy', sub: 'Mọi step', render() { return runBoard(true); } },
    {
      id: 'trace', nm: 'Truy cứu MO', sub: 'Vòng · bước · nhật ký',
      render() { return traceView(); }
    }
  ];

  /* ═══════════════════════════════════════════════════════════
     Màn dùng chung
     ═══════════════════════════════════════════════════════════ */

  /* §7.2 — Bảng đang chạy. can=false thì khoá nút và gắn dải cảnh báo. */
  function runBoard(can) {
    const list = M.MOS.filter(m => m.step === 4);
    const rows = list.map(m => {
      const st = m.runSt === 'RUN' ? '<span class="bdg ok"><span class="pulse"></span>Đang lắp ráp</span>'
        : m.runSt === 'HOLD' ? '<span class="bdg bad">ĐANG DỪNG ' + m.holdLine + '</span>'
          : '<span class="bdg">Hoàn thành</span>';
      const kpi = m.kpi === 'over'
        ? '<span class="bdg bad">Quá giờ ' + m.late + '</span>'
        : '<span class="bdg ok">Đạt</span>';
      const sl = m.sxOk != null
        ? '<span class="bdg ' + (m.sxOk >= m.qty - m.done ? 'ok' : 'warn') + '">Đạt ' + nf(m.sxOk) + '/' + nf(m.qty - m.done) + '</span>'
        : '<span class="bdg">Chưa xong SX</span>';
      const act = m.runSt === 'RUN' ? '<button class="btn sm danger">Dừng</button><button class="btn sm primary" data-go="prod/close">Hoàn thành</button>'
        : m.runSt === 'HOLD' ? '<button class="btn sm primary">Chạy lại</button>'
          : '<span class="dim" style="font-size:12px">đã chốt sổ</span>';
      return '<tr><td class="mono"><b>' + m.code + '</b></td><td>' + m.sp + '</td>' +
        '<td class="num">' + nf(m.qty - m.done) + '</td><td class="mono">' + m.lines + '</td>' +
        '<td class="mono">' + m.limit + '<br><em class="dim" style="font-size:10.5px;font-style:normal">vòng ' + m.round +
        ' · ' + nf(m.qty - m.done) + '/' + nf(m.qty) + '</em></td>' +
        '<td class="mono">' + m.wait + '</td><td class="mono">' + m.actual + '</td>' +
        '<td>' + st + (m.holdWhy ? '<br><em class="dim" style="font-size:10.5px;font-style:normal">' + m.holdWhy + '</em>' : '') + '</td>' +
        '<td>' + kpi + '</td><td>' + sl + '</td>' +
        '<td class="right"><div class="btnrow" style="justify-content:flex-end">' + act + '</div></td></tr>';
    }).join('');
    const body = tbl([{ t: 'MO' }, { t: 'Tên con hàng' }, { t: 'Số lượng', num: 1 }, { t: 'Line' }, { t: 'TG yêu cầu' },
    { t: 'TG chờ' }, { t: 'TG thực tế' }, { t: 'Hiện trạng Line' }, { t: 'Kết quả thời gian' }, { t: 'Sản lượng' }, { t: '' }], rows);
    const ro = can ? '' : '<div class="robar">👁 <b>Chỉ xem.</b> Vai của bạn xem được Step 4 nhưng không bấm được gì (§9b.4).</div>';
    return '<section class="panel' + (can ? '' : ' readonly') + '">' +
      '<header><h2>Bảng đang chạy</h2><span class="meta">' + list.length + ' MO · 1 MO 1 dòng</span></header>' +
      ro + '<div class="body flush">' + body + '</div></section>' +
      '<div class="note"><b><code>TG chờ</code> chạy khi Chờ xử lý, dừng khi sang Đang lắp ráp.</b> ' +
      '<code>TG thực tế</code> = tổng các đoạn Đang lắp ráp. Bấm <code>Dừng</code> thì đồng hồ này đứng, <code>TG chờ</code> chạy tiếp — ' +
      'thời gian dừng máy <b>tự động không tính</b> vào TG thực tế [22A].</div>' +
      '<div class="note warn"><b>Không gọi phần chênh là "Thiếu".</b> Từ <i>thiếu</i> đã có nghĩa riêng ở §7.5 — ' +
      'SL không làm ra được. Phần chênh <code>mục tiêu − đạt</code> gồm <b>cả hỏng lẫn thiếu</b>. ' +
      'Gọi trùng tên thì bảng báo <code>Thiếu 1.000</code> trong khi người vận hành vừa khai <i>thiếu 500</i>, đọc vào tưởng hệ thống tính sai.</div>' +
      '<div class="note"><b>Không tách hỏng/thiếu ngay trong bảng.</b> Đây là bảng <b>treo tường</b>, liếc để biết đơn nào chưa đủ. ' +
      'Hỏng bao nhiêu · thiếu bao nhiêu · vì sao là câu hỏi thứ hai — bấm vào MO xem bảng <b>Các vòng</b>.</div>' +
      '<div class="note ok"><b>§9b.5 — Bảng đang chạy là ngoại lệ về phạm vi xem:</b> hiện MO ở <b>mọi step</b> và ' +
      '<b>mọi phòng ban đều xem được</b>. Cái bị giới hạn là màn hình <b>thao tác</b> của từng step. ' +
      'Giấu bớt thì mỗi tổ mù về công đoạn trước và sau mình, gọi điện hỏi nhau nhiều hơn.</div>';
  }

  /* §9 — Truy cứu theo MO: 4 tầng */
  function traceView() {
    const rr = M.ROUNDS.map(r =>
      '<tr' + (r.live ? ' class="hl"' : '') + '><td><b>Vòng ' + r.r + '</b>' +
      (r.live ? ' <span class="bdg acc">đang chạy</span>' : '') + '</td>' +
      '<td class="mono">' + r.from + '</td><td class="mono">' + r.doneAt + '</td>' +
      '<td class="num">' + nf(r.ok) + '</td><td class="num">' + nf(r.ng) + '</td>' +
      '<td class="num">' + nf(r.short) + '</td><td class="num">' + nf(r.packed) + '</td>' +
      '<td class="dim">' + r.ngWhy + '</td><td class="dim">' + r.shortWhy + '</td>' +
      '<td class="dim">' + r.packNote + '</td>' +
      '<td' + (r.live ? ' class="dim"' : '') + '>' + (r.live ? '<i>' + r.ret + '</i>' : r.ret) + '</td></tr>').join('');

    const tt = M.TIMERS.map(t =>
      '<tr><td>' + t.step + (t.n > 1 ? ' <span class="bdg">' + t.n + ' vòng</span>' : '') + '</td>' +
      '<td>' + t.by + '</td><td class="mono">' + t.at + '</td><td class="mono">' + t.dur + '</td></tr>').join('');

    const lg = M.LOG.map(l =>
      '<tr><td class="mono">' + l.day + '</td><td class="mono">' + l.at + '</td>' +
      '<td class="mono"><b>' + l.mo + '</b></td><td class="num">' + l.r + '</td><td>' + l.step + '</td>' +
      '<td><span class="bdg line">' + l.act + '</span></td>' +
      '<td class="mono dim">' + (l.from ? l.from + ' → ' + l.to : '—') + '</td>' +
      '<td>' + l.by + '</td><td class="dim">' + l.note + '</td></tr>').join('');

    return '<div class="tiles" style="margin-bottom:16px">' +
      tile('M068820', '10.000', 'SL kế hoạch', '') +
      tile('Đã xong', '8.000', 'qtyDone', 'ok') +
      tile('Còn lại', '2.000', 'qtyRemain — mục tiêu vòng 2', 'warn') +
      tile('SL hỏng cộng dồn', '200', 'qtyNgTotal · tỷ lệ phế 2%', 'bad') +
      tile('Vòng hiện tại', '2', 'trả lại lần 1', 'acc') +
      '</div>' +
      panel('1 · Các vòng — kể cả vòng đang chạy', '§6b.4',
        tbl([{ t: 'Vòng' }, { t: 'Bắt đầu từ' }, { t: 'Nhập kho xong' }, { t: 'SX đạt', num: 1 }, { t: 'SL hỏng', num: 1 },
        { t: 'SL thiếu', num: 1 }, { t: 'Đã đóng thùng', num: 1 }, { t: 'Lý do hỏng' }, { t: 'Lý do thiếu' },
        { t: 'Ghi chú đóng thùng' }, { t: 'Lý do trả lại' }], rr), true) +
      '<div class="note"><b>Số về cột số, chữ về cột chữ.</b> Bốn cột số đứng liền nhau để đọc lướt và cộng nhẩm được; ' +
      'ba cột lý do đứng liền nhau ở sau. <b>Ba cột số đầu cộng lại đúng bằng mục tiêu vòng</b> — ' +
      '<code>8.000 + 200 + 1.800 = 10.000</code>. Nhìn một dòng là đối soát được ngay.</div>' +
      '<div class="note"><b><code>Bắt đầu từ</code> đọc thẳng nơi vòng đó bắt đầu</b>, ghi lại ngay lúc mở vòng — ' +
      'không suy từ các bước đã đi. Cách suy cũ luôn đoán nhầm vòng vừa mở thành <i>Bàn team leader</i>, ' +
      'kể cả khi QC FAIL vừa trả nó về Kho.</div>' +
      panel('2 · Đi qua các bước — mỗi vòng một bảng', 'đang xem vòng 2',
        tbl([{ t: 'Bước' }, { t: 'Ai nhận' }, { t: 'Nhận lúc' }, { t: 'Mất bao lâu' }], tt), true) +
      '<div class="note"><b>Bảng Timer cộng dồn qua MỌI VÒNG</b>, kèm chú thích <code>n vòng</code> khi bước đó chạy nhiều lần. ' +
      'Trước đây bảng chỉ đọc vòng hiện tại, nên MO đi qua Setup hai lần mà vòng cuối bắt đầu từ Bàn team leader thì cột Setup hiện ' +
      '<code>—</code> — nhìn vào tưởng chưa từng setup.</div>' +
      '<div class="note">Bấm vào dòng <b>4 · Sản xuất</b> thì bung ra hai bảng của <b>chính vòng đó</b>: ' +
      '<i>Năng suất từng line</i> và <i>Sản lượng theo giờ</i>. Chỉ bung khi bấm — để mở sẵn thì bảng dài gấp đôi, ' +
      'mà phần lớn lúc người ta chỉ liếc giờ giấc các bước.</div>' +
      panel('3 · Nhật ký đầy đủ', M.LOG.length + ' bản ghi · append-only',
        tbl([{ t: 'Ngày' }, { t: 'Giờ' }, { t: 'MO' }, { t: 'Vòng', num: 1 }, { t: 'Bước' },
        { t: 'Action' }, { t: 'from → to' }, { t: 'Người' }, { t: 'Lý do / metadata' }], lg), true) +
      '<div class="note"><b>[25A] History append-only, giữ vĩnh viễn.</b> Mỗi action ghi ' +
      '<code>MO, round, step, action, user, timestamp, from→to, reason, metadata</code>.</div>';
  }

  /* ── Tiện ích nhỏ ───────────────────────────────────────── */
  function tile(lb, vl, sub, cls) {
    return '<div class="tile ' + (cls || '') + '"><div class="lb">' + lb + '</div>' +
      '<div class="vl">' + (typeof vl === 'number' ? nf(vl) : vl) + '</div>' +
      '<div class="sub">' + (sub || '') + '</div></div>';
  }
  function fld(lb, ctl, hint) {
    return '<div class="field"><label>' + lb + '</label>' + ctl +
      (hint ? '<span class="hint">' + hint + '</span>' : '') + '</div>';
  }

  /* Màn Step 4 chỉ-xem, dành cho các phòng ban không phải SX/Bàn TL */
  function step4View() {
    return '<div class="pg-head"><span class="kicker">Step 4 · xem chung</span>' +
      '<h1>Sản xuất &amp; Đóng thùng</h1>' +
      '<p>Mọi phòng ban đều xem được Step 4 — kể cả Đóng thùng. Sản xuất là chỗ quyết định tiến độ, ' +
      'nên cả xưởng cần biết MO đang chạy chuyền nào và đã đóng thùng được bao nhiêu. Nhưng chỉ xem, không bấm được gì.</p></div>' +
      runBoard(false) +
      '<div class="note">Đóng thùng là <b>số cuối cùng trước khi hàng về kho</b>, nên Kho nhập cần thấy để biết sắp nhận bao nhiêu; ' +
      'QC và Setup cần thấy để biết lô mình làm đã ra thành phẩm chưa. Giấu bớt thì cả xưởng phải gọi điện hỏi nhau.</div>';
  }

  /* ── Luồng rẽ nhánh (§7b) ───────────────────────────────────
     Step 4 KHÔNG phải một dãy bước nối đuôi. Ba bước đầu tuần tự
     thật; từ lúc bấm "Đang lắp ráp" thì tách hai nhánh chạy cùng
     lúc, hai timer riêng. Ràng buộc thứ tự duy nhất giữa hai nhánh
     là: Kết thúc đóng thùng phải sau Chốt sổ SX.

     Vẽ thành 1→7 là bịa ra 5 ràng buộc không có, đồng thời giấu mất
     đúng cái ràng buộc có thật. */
  const FLOW = {
    prod: {
      seq: ['scan', 'pickline', 'board'],
      forkNote: 'bấm “Đang lắp ráp” là mở cả hai nhánh',
      lanes: [
        { nm: 'Chuyền', ids: ['hourly', 'close'] },
        { nm: 'Đóng thùng', ids: ['packing', 'packclose'] }
      ]
    }
  };

  M.FLOW = FLOW;
  M.SCREENS = { wh_out: WH_OUT, setup: SETUP, qc: QC, waiting: WAITING, prod: PROD, wh_in: WH_IN, planner: PLANNER };
  M.runBoard = runBoard;
  M.step4View = step4View;
  M.traceView = traceView;
  /* Quy tắc đọc mã gom về một chỗ (trang Luồng) thay vì lặp lại ở cả
     sáu trạm — cùng một bộ luật, đọc một lần là đủ. */
  M.ui = { panel, empty, tbl, tile, fld, badges, scanRules };
})(window.MES);
