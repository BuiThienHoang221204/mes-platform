"use client";

import { useRef } from "react";

/**
 * Ô quét: Enter là gửi đi. KHÔNG tự giành tiêu điểm.
 *
 * Bản trước bám theo FE-PLAN §1 — tự lấy tiêu điểm lúc mở màn, rồi cứ 1,2 giây và
 * sau MỌI cú bấm chuột lại giành về. Lý do khi đó là đầu đọc QR gõ như bàn phím:
 * mất tiêu điểm một nhịp là ký tự rơi ra ngoài và lần quét mất trắng.
 *
 * Cái giá quá đắt: không ai bấm được vào chỗ khác trên màn quá 1,2 giây — chọn
 * một dòng hàng đợi, kéo thanh cuộn, bấm nút nào cũng bị con trỏ giật về ô quét.
 * Và trên điện thoại, giành tiêu điểm là bàn phím ảo bật lên che nửa màn hình.
 *
 * FE-REBUILD §9 chốt người vận hành cầm điện thoại và quét bằng camera, nên đầu
 * đọc gắn ngoài không còn là đường chính. Ai dùng đầu đọc thì bấm vào ô một lần
 * rồi quét — mất một chạm, đổi lại cả màn hình dùng được bình thường.
 */
export function useScanInput(onSubmit: (raw: string) => void) {
  const ref = useRef<HTMLInputElement>(null);

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const raw = e.currentTarget.value.trim();
    if (!raw) return;
    e.currentTarget.value = "";
    onSubmit(raw);
  };

  return { ref, onKeyDown };
}
