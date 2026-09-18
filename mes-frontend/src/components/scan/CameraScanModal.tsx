"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { BrandMark } from "@/components/common/BrandMark";
import { CaretLeft, Copy, ImageSquare, Minus, Plus } from "@/components/common/PhosphorIcons";

const BOX_ID = "mes-camera-scan";
const FILE_BOX_ID = "mes-camera-file";

/* Thử lần lượt cho tới khi mở được. `facingMode: "environment"` trần là ràng buộc
   MỀM — máy nào không khớp thì trình duyệt tự rơi về camera trước mà không báo lỗi,
   nên điện thoại quét QR lại soi vào mặt người dùng. `exact` mới ép được.

   Nới dần chứ không chỉ dùng `exact`: `exact` ném `OverconstrainedError` ở máy chỉ
   có webcam trước, và ở đó mở camera trước vẫn tốt hơn là không mở được gì. */
const CAMERA_TRIES: MediaTrackConstraints[] = [
  { facingMode: { exact: "environment" } },
  { facingMode: "environment" },
  { facingMode: "user" },
];

const CORNER = "absolute h-9 w-9 border-white";
const PILL_BTN =
  "flex min-h-touch flex-1 cursor-pointer items-center justify-center gap-2 px-3 text-body-sm text-white";

type Zoom = { min: number; max: number; step: number; value: number };

type Props = {
  open: boolean;
  onClose: () => void;
  onRead: (raw: string) => void;
};

export function CameraScanModal({ open, onClose, onRead }: Props) {
  const [problem, setProblem] = useState<string | null>(null);
  const [hint, setHint] = useState<string | null>(null);
  const [zoom, setZoom] = useState<Zoom | null>(null);
  const [host, setHost] = useState<HTMLElement | null>(null);

  const trackRef = useRef<MediaStreamTrack | null>(null);
  const onReadRef = useRef(onRead);
  const onCloseRef = useRef(onClose);
  useEffect(() => {
    onReadRef.current = onRead;
    onCloseRef.current = onClose;
  });

  useEffect(() => setHost(document.body), []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseRef.current();
    };
    const before = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = before;
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;

    let alive = true;
    let scanner: import("html5-qrcode").Html5Qrcode | null = null;
    let stream: MediaStream | null = null;
    setProblem(null);
    setHint(null);
    setZoom(null);

    const killTracks = () => {
      stream?.getTracks().forEach((t) => t.stop());
      stream = null;
      trackRef.current = null;
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

        const config = {
          fps: 10,
          qrbox: (w: number, h: number) => {
            const side = Math.floor(Math.min(w, h) * 0.7);
            return { width: side, height: side };
          },
        };
        const onDecoded = (text: string) => {
          onReadRef.current(text);
          onCloseRef.current();
        };
        const onFrameMiss = () => {
          /* mỗi khung hình không đọc được đều gọi vào đây — bỏ qua */
        };

        let opened = false;
        let lastError: unknown = null;
        for (const camera of CAMERA_TRIES) {
          if (!alive) break;
          try {
            await scanner.start(camera, config, onDecoded, onFrameMiss);
            opened = true;
            break;
          } catch (e) {
            lastError = e;
          }
        }
        if (!opened) throw lastError ?? new Error("no camera");
        const video = document.querySelector<HTMLVideoElement>(`#${BOX_ID} video`);
        if (video?.srcObject instanceof MediaStream) stream = video.srcObject;

        // Thanh phóng to chỉ dựng khi camera THẬT SỰ nhận được. Webcam máy bàn hầu
        // hết không có `zoom` — vẽ ra một thanh trượt kéo không ăn thua là nói dối.
        const track = stream?.getVideoTracks()[0] ?? null;
        trackRef.current = track;
        const caps = track?.getCapabilities?.() as
          | { zoom?: { min: number; max: number; step?: number } }
          | undefined;
        const now = track?.getSettings?.() as { zoom?: number } | undefined;
        if (alive && caps?.zoom) {
          setZoom({
            min: caps.zoom.min,
            max: caps.zoom.max,
            step: caps.zoom.step || 0.1,
            value: now?.zoom ?? caps.zoom.min,
          });
        }

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

  const applyZoom = useCallback((value: number) => {
    setZoom((z) => (z ? { ...z, value } : z));
    const track = trackRef.current;
    if (!track) return;
    void track
      .applyConstraints({ advanced: [{ zoom: value } as unknown as MediaTrackConstraintSet] })
      .catch(() => {});
  }, []);

  const pasteCode = useCallback(async () => {
    setHint(null);
    try {
      const text = (await navigator.clipboard.readText()).trim();
      if (!text) {
        setHint("Bộ nhớ tạm đang trống.");
        return;
      }
      onReadRef.current(text);
      onCloseRef.current();
    } catch {
      setHint("Trình duyệt không cho đọc bộ nhớ tạm — dán thẳng vào ô quét ở màn trước.");
    }
  }, []);

  const readFile = useCallback(async (file: File) => {
    setHint(null);
    try {
      const { Html5Qrcode } = await import("html5-qrcode");
      const reader = new Html5Qrcode(FILE_BOX_ID);
      const text = await reader.scanFile(file, false);
      try {
        reader.clear();
      } catch {
      }
      onReadRef.current(text);
      onCloseRef.current();
    } catch {
      setHint("Không tìm thấy mã QR trong ảnh này.");
    }
  }, []);

  if (!open || !host) return null;

  return createPortal(
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Quét bằng camera"
      className="fixed inset-0 z-[60] bg-black"
    >
      <div
        id={BOX_ID}
        className="!absolute !inset-0 [&_#qr-shaded-region]:!hidden [&_video]:!h-full [&_video]:!w-full [&_video]:!object-cover"
      />
      <div id={FILE_BOX_ID} className="hidden" />

      {problem ? null : (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="relative h-[min(70vw,70vh,360px)] w-[min(70vw,70vh,360px)] shadow-[0_0_0_100vmax_rgba(0,0,0,0.62)]">
            <span className={`${CORNER} -left-1 -top-1 rounded-tl-lg border-l-4 border-t-4`} />
            <span className={`${CORNER} -right-1 -top-1 rounded-tr-lg border-r-4 border-t-4`} />
            <span className={`${CORNER} -bottom-1 -left-1 rounded-bl-lg border-b-4 border-l-4`} />
            <span className={`${CORNER} -bottom-1 -right-1 rounded-br-lg border-b-4 border-r-4`} />
            <span className="absolute inset-0 overflow-hidden rounded-md">
              <span className="scan-sweep absolute inset-x-0 -translate-y-full">
                <span className="block h-24 w-full bg-gradient-to-t from-white/30 via-white/10 to-transparent blur-[2px]" />
                <span className="block h-[2px] w-full bg-white shadow-[0_0_20px_6px_rgba(255,255,255,0.6)]" />
              </span>
            </span>
          </div>
        </div>
      )}

      <div className="absolute inset-x-0 top-0 px-3 pt-[calc(1.25rem+env(safe-area-inset-top))]">
        <button
          type="button"
          onClick={onClose}
          aria-label="Đóng máy quét"
          className="absolute left-3 top-[calc(1.25rem+env(safe-area-inset-top))] flex h-11 w-11 items-center justify-center rounded-pill bg-white/15 text-white backdrop-blur-sm"
        >
          <CaretLeft size={24} weight="bold" />
        </button>

        <div className="pointer-events-none flex flex-col items-center gap-2 px-14">
          <BrandMark className="h-7 w-auto text-white" />
          <p className="text-center text-body-sm text-white/75">Quét mã QR để nhận lệnh vào trạm</p>
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 space-y-3 px-4 pb-[calc(1.25rem+env(safe-area-inset-bottom))]">
        {problem ? (
          <p className="rounded-card bg-danger-soft px-4 py-3 text-center text-body-sm text-danger">
            {problem}
          </p>
        ) : (
          <p className="text-center text-body-sm text-white/70">
            {hint ?? "Đưa mã vào khung — đọc được là nhận MO luôn."}
          </p>
        )}

        <div className="flex items-center rounded-pill bg-white/15 backdrop-blur-sm">
          <button type="button" onClick={pasteCode} className={PILL_BTN}>
            <Copy size={20} />
            Dán mã QR
          </button>
          <span aria-hidden className="h-6 w-px shrink-0 bg-white/30" />
          <label className={PILL_BTN}>
            <ImageSquare size={20} />
            Chọn QR từ ảnh
            <input
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                e.target.value = "";
                if (file) void readFile(file);
              }}
            />
          </label>
        </div>

        {zoom ? (
          <div className="flex items-center gap-3 px-2 text-white">
            <Minus size={20} aria-hidden />
            <input
              type="range"
              aria-label="Phóng to"
              min={zoom.min}
              max={zoom.max}
              step={zoom.step}
              value={zoom.value}
              onChange={(e) => applyZoom(Number(e.target.value))}
              className="h-1 min-w-0 flex-1 cursor-pointer appearance-none rounded-pill bg-white/30 accent-white"
            />
            <Plus size={20} aria-hidden />
          </div>
        ) : null}
      </div>
    </div>,
    host,
  );
}
