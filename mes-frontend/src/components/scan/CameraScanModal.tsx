"use client";

import { useEffect, useRef, useState } from "react";

import { AppModal } from "@/components/ui/AppModal";
import { Note } from "@/components/ui/Note";

const BOX_ID = "mes-camera-scan";

type Props = {
  open: boolean;
  onClose: () => void;
  onRead: (raw: string) => void;
};

export function CameraScanModal({ open, onClose, onRead }: Props) {
  const [problem, setProblem] = useState<string | null>(null);

  const onReadRef = useRef(onRead);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onReadRef.current = onRead;
    onCloseRef.current = onClose;
  });

  useEffect(() => {
    if (!open) return;

    let alive = true;
    let scanner: import("html5-qrcode").Html5Qrcode | null = null;
    let stream: MediaStream | null = null;
    setProblem(null);

    const killTracks = () => {
      stream?.getTracks().forEach((t) => t.stop());
      stream = null;
      document.querySelectorAll<HTMLVideoElement>(`#${BOX_ID} video`).forEach((v) => {
        const s = v.srcObject;
        if (s instanceof MediaStream) s.getTracks().forEach((t) => t.stop());
        v.srcObject = null;
      });
    };

    const stop = async () => {
      killTracks();
      if (!scanner) return;
      try {
        await scanner.stop();
      } catch {
      }
      try {
        scanner.clear();
      } catch {
      }
      killTracks();
    };

    (async () => {
      try {
        const { Html5Qrcode } = await import("html5-qrcode");
        if (!alive) return;
        scanner = new Html5Qrcode(BOX_ID);
        await scanner.start(
          { facingMode: "environment" },
          { fps: 10, qrbox: { width: 240, height: 240 } },
          (text) => {
            onReadRef.current(text);
            onCloseRef.current();
          },
          () => {
            /* mỗi khung hình không đọc được đều gọi vào đây — bỏ qua */
          },
        );
        const video = document.querySelector<HTMLVideoElement>(`#${BOX_ID} video`);
        if (video?.srcObject instanceof MediaStream) stream = video.srcObject;

        if (!alive) await stop();
      } catch {
        if (alive) setProblem("Không mở được camera. Kiểm tra quyền truy cập của trình duyệt.");
      }
    })();

    return () => {
      alive = false;
      void stop();
    };
  }, [open]);

  return (
    <AppModal open={open} title="Quét bằng camera" onClose={onClose}>
      <div className="space-y-4">
        <div
          id={BOX_ID}
          className="mx-auto aspect-square w-full max-w-sm overflow-hidden rounded-card bg-surface-2"
        />
        {problem ? (
          <Note tone="danger">{problem}</Note>
        ) : (
          <p className="text-center text-body-sm text-fg-muted">
            Đưa mã QR vào khung. Đọc được là tự đóng và điền vào ô quét.
          </p>
        )}
        <Note>
          Máy có đầu đọc gắn ngoài thì không cần mở camera — đầu đọc gõ thẳng vào ô quét rồi tự
          bấm Enter, nhanh hơn hẳn.
        </Note>
      </div>
    </AppModal>
  );
}
