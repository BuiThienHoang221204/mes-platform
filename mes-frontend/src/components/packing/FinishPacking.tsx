"use client";

import { useState } from "react";

import { BoxTally } from "@/components/packing/BoxTally";
import { AppButton } from "@/components/ui/AppButton";
import { AppInput } from "@/components/ui/AppInput";
import { ChoiceCard } from "@/components/ui/ChoiceCard";
import { Note } from "@/components/ui/Note";
import { nfmt } from "@/utils/format";
import { boxBreakdown, type BoxReconcile } from "@/utils/packing";

type Props = {
  box: BoxReconcile;
  pcsPerBox: number;
  busy?: boolean;
  onLogBoxes: (boxes: number) => void;
  onFinish: (qty: number, note: string) => void;
};

/**
 * Chốt sổ đóng thùng — thao tác KHÔNG hoàn tác được của trạm 4.
 *
 * Mặc định là TOÀN BỘ số đã làm ra, không phải số thùng đầy đã ghi sổ giờ. BRD
 * §7b.2: "Thùng cuối của đơn được đóng THIẾU — đó là mặc định, không phải ngoại
 * lệ", nên phần lẻ luôn vào được thùng cuối và cuối vòng hai số bằng nhau.
 *
 * Màn hình cũ mặc định bằng `packed_pcs` (chỉ thùng đầy đã ghi sổ) và submit
 * trống thì lấy luôn số đó — lệnh làm ra 2.500 ghi sổ 2.400 thì 100 pcs nằm
 * trong thùng lẻ bị khai thành hàng THIẾU, và hệ thống mở vòng 2 để làm bù.
 *
 * Chỉ khi người dùng CHỦ ĐỘNG gõ ít hơn số làm ra mới hỏi lại — đó là tình huống
 * duy nhất BRD §10 #38 giữ ô nhập này: hết ca mà hàng đạt còn nằm trên bàn.
 */
export function FinishPacking({ box, pcsPerBox, busy, onLogBoxes, onFinish }: Props) {
  const [qty, setQty] = useState(String(box.madePcs));
  const [note, setNote] = useState("");
  const [confirmShort, setConfirmShort] = useState(false);

  const n = Number(qty);
  const valid = Number.isFinite(n) && n > 0;
  const short = valid ? box.madePcs - n : 0;
  const parts = boxBreakdown(valid ? n : 0, pcsPerBox);

  return (
    <div className="space-y-3">
      <BoxTally box={box} showTotal />

      {box.unloggedBoxes ? (
        <Note tone="warn">
          <strong>Sổ giờ đang chạy sau thực tế {box.unloggedBoxes} thùng đầy.</strong> Số chốt
          dưới đây mới là số vào kho, nên chốt vẫn đúng. Ghi bù cho sổ giờ khớp lại thì báo cáo
          sản lượng theo giờ mới đọc được.
          <br />
          <button
            type="button"
            disabled={busy}
            onClick={() => onLogBoxes(box.unloggedBoxes)}
            className="mt-1 underline disabled:opacity-45"
          >
            Ghi bù {box.unloggedBoxes} thùng vào sổ giờ
          </button>
        </Note>
      ) : box.loosePcs ? (
        <Note>
          Chênh {nfmt(box.loosePcs)} pcs là <strong>phần chưa đủ một thùng đầy</strong>. Sổ giờ
          chỉ đếm thùng đầy nên nó không nằm ở đó — nó vào <strong>thùng lẻ cuối</strong> ngay
          bây giờ. Thùng cuối đóng thiếu là mặc định, không phải ngoại lệ.
        </Note>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <AppInput
          label="Tổng pcs đã đóng thùng"
          type="number"
          inputMode="numeric"
          value={qty}
          onChange={(e) => {
            setQty(e.target.value);
            setConfirmShort(false);
          }}
          hint={
            pcsPerBox > 0 && valid
              ? `${nfmt(n)} pcs = ${parts.full} thùng đầy${parts.last ? ` + 1 thùng lẻ ${nfmt(parts.last)}` : ""}`
              : "gõ số pcs thật sự đã vào thùng"
          }
        />
        <AppInput label="Ghi chú" value={note} onChange={(e) => setNote(e.target.value)} />
      </div>

      {short > 0 ? (
        <>
          <Note tone="warn">
            <strong>Bạn đang khai ít hơn số làm ra {nfmt(short)} pcs.</strong> Chốt vậy thì{" "}
            {nfmt(short)} pcs này thành <strong>hàng thiếu</strong> và hệ thống mở{" "}
            <strong>vòng 2</strong> để làm bù. Không hoàn tác được.
            <br />
            Chỉ đúng khi <strong>hết ca mà hàng đạt còn nằm trên bàn chưa đóng</strong>. Phần
            chưa đủ một thùng thì không tính — nó vào thùng lẻ cuối.
          </Note>
          <ChoiceCard
            selected={!confirmShort}
            title={`Đóng hết ${nfmt(box.madePcs)} pcs`}
            hint="Trường hợp thường gặp — thùng cuối đóng thiếu, vòng đóng lại, không phải làm bù."
            onSelect={() => {
              setQty(String(box.madePcs));
              setConfirmShort(false);
            }}
          />
          <ChoiceCard
            selected={confirmShort}
            title={`Chỉ đóng ${nfmt(n)} pcs — ${nfmt(short)} làm bù ở vòng sau`}
            hint="Hàng đạt còn trên bàn chưa đóng thùng được."
            onSelect={() => setConfirmShort(true)}
          />
        </>
      ) : null}

      <AppButton
        variant={short > 0 ? "danger" : "primary"}
        disabled={busy || !valid || (short > 0 && !confirmShort)}
        onClick={() => onFinish(n, note)}
      >
        Kết thúc đóng thùng{valid ? ` · ${nfmt(n)} pcs` : ""}
      </AppButton>

      {short > 0 && !confirmShort ? (
        <p className="text-caption text-fg-subtle">
          Nút khoá cho tới khi bạn chọn rõ một dòng ở trên — không có mặc định im lặng.
        </p>
      ) : null}
    </div>
  );
}
