"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { BrandMark } from "@/components/common/BrandMark";
import { CaretLeft, Copy, ImageSquare, Minus, Plus } from "@/components/common/PhosphorIcons";

const VIEWFINDER_WIDTH = 1280;

const BOX_ID = "mes-camera-scan";
const FILE_BOX_ID = "mes-camera-file";

const CAMERA_TRIES: MediaTrackConstraints[] = [
  { facingMode: { exact: "environment" } },
  { facingMode: "environment" },
  { facingMode: "user" },
];

function cameraFailureMessage(err: unknown): string {
  const text = String((err as Error)?.message ?? err ?? "");
  if (text.includes("NotAllowedError") || text.includes("PermissionDenied"))
    return "Trình duyệt đang CHẶN camera ở trang này. Bấm biểu tượng ổ khoá cạnh thanh địa chỉ → bật Camera → tải lại trang.";
  if (
    text.includes("NotFoundError") ||
    text.includes("DevicesNotFound") ||
    text.includes("OverconstrainedError")
  )
    return "Máy này không có camera nào dùng được. Cắm webcam, hoặc mở trang bằng điện thoại.";
  if (text.includes("NotReadableError") || text.includes("TrackStartError"))
    return "Camera đang bị ứng dụng khác chiếm (Zoom, Teams, Camera…). Đóng ứng dụng đó rồi mở lại.";
  if (text.includes("SecurityError"))
    return "Trang phải chạy qua HTTPS mới mở được camera.";
  return `Không mở được camera — ${text || "không rõ lý do"}`;
}

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
  const [scale, setScale] = useState(0);
  const [view, setView] = useState<{ w: number; h: number } | null>(null);

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
          experimentalFeatures: { useBarCodeDetectorIfSupported: true },
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
            await scanner.start(
              camera,
              { ...config, videoConstraints: { ...camera, width: { ideal: 1920 }, height: { ideal: 1080 } } },
              onDecoded,
              onFrameMiss,
            );
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
      } catch (e) {
        if (alive) setProblem(cameraFailureMessage(e));
      }
    })();

    return () => {
      alive = false;
      void stop();
    };
  }, [open]);

  /* Vòng giải mã THỨ HAI, chạy song song với `html5-qrcode`.
   *
   *  Đo trên ba ảnh nhãn thật người vận hành chụp (QR dày, giấy cong, chụp nghiêng):
   *  bộ giải của `html5-qrcode` đọc được 0/3, `zxing-wasm` 0/3, còn `jsQR` 2/3.
   *  Nên không thay bộ nào cả — chạy thêm một bộ nữa, ai đọc ra trước thì thắng.
   *
   *  Đọc thẳng từ `videoWidth × videoHeight`, tức độ phân giải GỐC của cảm biến,
   *  không qua canvas hiển thị. Và KHÔNG phóng to: đo được là phóng to làm jsQR
   *  hỏng hẳn — bộ nhị phân hoá của nó chia ô theo kích thước cố định, ảnh to lên
   *  thì mỗi ô không còn trùm đủ một ô mã nữa. */
  useEffect(() => {
    if (!open) return;
    let alive = true;
    let busy = false;
    let done = false;
    const canvas = document.createElement("canvas");
    const ctx2d = canvas.getContext("2d", { willReadFrequently: true });

    const tick = async () => {
      if (!alive || busy || done || !ctx2d) return;
      const v = document.querySelector<HTMLVideoElement>(`#${BOX_ID} video`);
      if (!v?.videoWidth) return;
      busy = true;
      try {
        canvas.width = v.videoWidth;
        canvas.height = v.videoHeight;
        ctx2d.drawImage(v, 0, 0);
        const frame = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
        const { default: jsQR } = await import("jsqr");
        const hit = jsQR(frame.data, frame.width, frame.height, { inversionAttempts: "dontInvert" });
        if (hit?.data && alive && !done) {
          done = true;
          onReadRef.current(hit.data);
          onCloseRef.current();
        }
      } catch {
        /* khung hình lỗi thì bỏ qua, khung sau thử lại */
      } finally {
        busy = false;
      }
    };

    const timer = setInterval(tick, 350);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [open]);

  /* Thu khung ngắm cho vừa màn. Đo SAU khi camera lên hình vì chiều cao thẻ video
     chỉ biết được khi đã có tỷ lệ của luồng. */
  useEffect(() => {
    if (!open) return;
    let alive = true;
    const fit = () => {
      const v = document.querySelector<HTMLVideoElement>(`#${BOX_ID} video`);
      if (!v || !v.clientWidth || !v.clientHeight) return false;
      const k = Math.min(window.innerWidth / v.clientWidth, window.innerHeight / v.clientHeight);
      if (alive) {
        setScale(k);
        setView({ w: v.clientWidth * k, h: v.clientHeight * k });
      }
      return true;
    };
    const timer = setInterval(() => {
      if (fit()) clearInterval(timer);
    }, 120);
    window.addEventListener("resize", fit);
    window.addEventListener("orientationchange", fit);
    return () => {
      alive = false;
      clearInterval(timer);
      window.removeEventListener("resize", fit);
      window.removeEventListener("orientationchange", fit);
      setScale(0);
      setView(null);
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

    // jsQR TRƯỚC: trên ảnh nhãn chụp thật nó đọc được 2/3, bộ của html5-qrcode 0/3.
    try {
      const bitmap = await createImageBitmap(file);
      const canvas = document.createElement("canvas");
      canvas.width = bitmap.width;
      canvas.height = bitmap.height;
      const ctx2d = canvas.getContext("2d", { willReadFrequently: true });
      if (ctx2d) {
        ctx2d.drawImage(bitmap, 0, 0);
        const frame = ctx2d.getImageData(0, 0, canvas.width, canvas.height);
        const { default: jsQR } = await import("jsqr");
        const hit = jsQR(frame.data, frame.width, frame.height, { inversionAttempts: "attemptBoth" });
        if (hit?.data) {
          onReadRef.current(hit.data);
          onCloseRef.current();
          return;
        }
      }
    } catch {
      /* rơi xuống bộ dưới */
    }

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
      <div className="absolute inset-0 overflow-hidden">
        <div
          className="absolute left-1/2 top-1/2 origin-center transition-opacity duration-200"
          style={{
            width: VIEWFINDER_WIDTH,
            transform: `translate(-50%, -50%) scale(${scale || 0.3})`,
            opacity: scale ? 1 : 0,
          }}
        >
          <div id={BOX_ID} className="w-full" />
        </div>
      </div>

      {/* Khung ngắm nằm NGOÀI lớp bị thu nhỏ, và lấy kích thước video đang hiển thị
          thật. Để nó bên trong thì nó co theo `scale` và chỉ còn bằng đầu ngón tay. */}
      {problem || !view ? null : (
        <div
          className="pointer-events-none absolute left-1/2 top-1/2 flex -translate-x-1/2 -translate-y-1/2 items-center justify-center"
          style={{ width: view.w, height: view.h }}
        >
          <div className="relative aspect-square h-[72%] max-h-[320px]">
            <span className={`${CORNER} -left-1 -top-1 rounded-tl-lg border-l-4 border-t-4`} />
            <span className={`${CORNER} -right-1 -top-1 rounded-tr-lg border-r-4 border-t-4`} />
            <span className={`${CORNER} -bottom-1 -left-1 rounded-bl-lg border-b-4 border-l-4`} />
            <span className={`${CORNER} -bottom-1 -right-1 rounded-br-lg border-b-4 border-r-4`} />
            <span className="absolute inset-0 overflow-hidden rounded-md">
              <span className="scan-sweep absolute inset-x-0 -translate-y-full">
                <span className="block h-24 w-full bg-gradient-to-t from-white/25 via-white/10 to-transparent blur-[2px]" />
                <span className="block h-[2px] w-full bg-white shadow-[0_0_20px_6px_rgba(255,255,255,0.6)]" />
              </span>
            </span>
          </div>
        </div>
      )}
      <div id={FILE_BOX_ID} className="hidden" />

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
