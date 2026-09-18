"use client";

import { useRef } from "react";

import { CalendarBlank } from "@/components/common/PhosphorIcons";
import { ControlFace, controlBox } from "@/components/ui/ControlShell";
import { dmy } from "@/utils/dateRange";

type Props = {
  label?: string;
  value: string;
  onChange: (v: string) => void;
  min?: string;
  max?: string;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
};

export function AppDate({
  label,
  value,
  onChange,
  min,
  max,
  disabled,
  className = "",
  placeholder = "Chọn ngày",
}: Props) {
  const input = useRef<HTMLInputElement>(null);

  const openPicker = () => {
    const el = input.current;
    if (!el || el.disabled) return;
    try {
      el.showPicker();
    } catch (e) {
      void e;
    }
  };

  return (
    <div className={`relative ${controlBox(label, disabled, className)} focus-within:border-accent`}>
      <ControlFace label={label} mono icon={<CalendarBlank size={20} />}>
        {value ? dmy(value) : <span className="text-fg-subtle">{placeholder}</span>}
      </ControlFace>

      <input
        ref={input}
        type="date"
        aria-label={label}
        value={value}
        min={min}
        max={max}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        onClick={openPicker}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openPicker();
          }
        }}
        className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
      />
    </div>
  );
}
