"use client";

import { Minus, Plus } from "@/components/common/PhosphorIcons";
import { FONT_SCALE_LABELS, FS_DEFAULT, useUiStore } from "@/stores/useUiStore";

const LAST = FONT_SCALE_LABELS.length - 1;
const STEP = "flex h-10 w-10 items-center justify-center rounded-pill text-fg-muted hover:bg-surface-2 hover:text-fg disabled:opacity-40 disabled:hover:bg-transparent";

export function FontScalePicker() {
  const fontStep = useUiStore((s) => s.fontStep);
  const setFontStep = useUiStore((s) => s.setFontStep);
  const increaseFont = useUiStore((s) => s.increaseFont);
  const decreaseFont = useUiStore((s) => s.decreaseFont);

  return (
    <div className="flex items-center gap-4">
      {fontStep === FS_DEFAULT ? null : (
        <button
          type="button"
          onClick={() => setFontStep(FS_DEFAULT)}
          className="text-body-sm text-accent underline underline-offset-4"
        >
          Về mặc định
        </button>
      )}

      <div className="flex items-center rounded-pill border border-line-strong">
        <button
          type="button"
          aria-label="Giảm cỡ chữ"
          disabled={fontStep === 0}
          onClick={decreaseFont}
          className={STEP}
        >
          <Minus size={18} />
        </button>
        <span
          aria-live="polite"
          className="min-w-16 text-center text-body-lg tnum font-semibold text-fg"
        >
          {FONT_SCALE_LABELS[fontStep]}
        </span>
        <button
          type="button"
          aria-label="Tăng cỡ chữ"
          disabled={fontStep === LAST}
          onClick={increaseFont}
          className={STEP}
        >
          <Plus size={18} />
        </button>
      </div>
    </div>
  );
}
