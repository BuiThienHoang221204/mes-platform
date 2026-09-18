"use client";

import { useState } from "react";
import { createPortal } from "react-dom";

import { CalendarBlank, CaretDown } from "@/components/common/PhosphorIcons";
import { AppButton } from "@/components/ui/AppButton";
import { AppDate } from "@/components/ui/AppDate";
import { ControlFace, controlBox } from "@/components/ui/ControlShell";
import { useAnchoredMenu } from "@/hooks/useAnchoredMenu";
import {
  PRESET_LABEL,
  PRESETS,
  rangeLabel,
  rangeOf,
  type DateRange,
  type RangePreset,
} from "@/utils/dateRange";

type Props = {
  label?: string;
  value: DateRange;
  onChange: (r: DateRange) => void;
};

const WIDTH = 240;

export function DateRangePicker({ label = "Khung thời gian", value, onChange }: Props) {
  const { spot, anchor, menu, toggle, close } = useAnchoredMenu(WIDTH);
  const [custom, setCustom] = useState(false);

  const pick = (p: RangePreset) => {
    if (p === "custom") {
      setCustom(true);
      return;
    }
    onChange(rangeOf(p) as DateRange);
    setCustom(false);
    close();
  };

  const panel = spot ? (
    <div
      ref={menu}
      style={{ top: spot.top, left: spot.left, width: spot.width }}
      className="fixed z-50 overflow-hidden rounded-card border border-line bg-surface shadow-lg"
    >
      <ul className="py-1">
        {PRESETS.map((p) => (
          <li key={p}>
            <button
              type="button"
              onClick={() => pick(p)}
              className="flex w-full items-center justify-between px-3 py-2 text-left text-body-sm text-fg hover:bg-surface-2"
            >
              {PRESET_LABEL[p]}
              {p === "custom" ? <CaretDown size={18} className="text-fg-subtle" /> : null}
            </button>
          </li>
        ))}
      </ul>

      {custom ? (
        <div className="space-y-2 border-t border-line bg-surface-2 p-2">
          <AppDate
            label="Từ ngày"
            className="w-full"
            value={value.from}
            max={value.to || undefined}
            onChange={(from) => onChange({ ...value, from })}
          />
          <AppDate
            label="Đến ngày"
            className="w-full"
            value={value.to}
            min={value.from || undefined}
            onChange={(to) => onChange({ ...value, to })}
          />
          <AppButton size="sm" block variant="primary" onClick={() => close()}>
            Xong
          </AppButton>
        </div>
      ) : null}

      {value.from || value.to ? (
        <div className="border-t border-line p-1.5">
          <AppButton
            size="sm"
            block
            onClick={() => {
              onChange({ from: "", to: "" });
              setCustom(false);
              close();
            }}
          >
            Bỏ lọc
          </AppButton>
        </div>
      ) : null}
    </div>
  ) : null;

  return (
    <>
      <button ref={anchor} type="button" onClick={toggle} className={controlBox(label, false, "w-full")}>
        <ControlFace label={label} mono icon={<CalendarBlank size={20} />}>
          {rangeLabel(value)}
        </ControlFace>
      </button>

      {panel ? createPortal(panel, document.body) : null}
    </>
  );
}
