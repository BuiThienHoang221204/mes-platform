"use client";

import { createPortal } from "react-dom";

import { CaretDown, Check } from "@/components/common/PhosphorIcons";
import { ControlFace, controlBox } from "@/components/ui/ControlShell";
import { useAnchoredMenu } from "@/hooks/useAnchoredMenu";

export type DropdownOption = { value: string; label: string; hint?: string };

type Props = {
  label?: string;
  value: string;
  options: DropdownOption[];
  onChange: (v: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
};

/**
 * Ô chọn tự vẽ, thay cho `<select>` của trình duyệt.
 *
 * `<select>` không nhận được CSS của app: danh sách xổ ra do hệ điều hành vẽ, nên
 * nó giữ nguyên phông, màu và khoảng cách của Windows — lạc hẳn giữa các ô khác,
 * và ở chế độ tối thì nền trắng chói.
 *
 * Đổi lại, tự vẽ thì phải tự lo bàn phím và đóng mở. `AppSelect` vẫn giữ cho các
 * biểu mẫu: ở đó `<select>` gốc lợi hơn vì bàn phím và trình đọc màn hình đã có sẵn.
 */
export function AppDropdown({
  label,
  value,
  options,
  onChange,
  placeholder = "Chọn…",
  disabled,
  className = "",
}: Props) {
  const { spot, open, anchor, menu, toggle, close } = useAnchoredMenu(180);
  const picked = options.find((o) => o.value === value);

  const pick = (v: string) => {
    onChange(v);
    close();
  };

  const panel = spot ? (
    <div
      ref={menu}
      style={{ top: spot.top, left: spot.left, width: spot.width }}
      className="fixed z-[70] overflow-hidden rounded-card border border-line bg-surface py-1 shadow-lg"
    >
      {options.map((o) => {
        const isPicked = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => pick(o.value)}
            className={`flex w-full items-center gap-2 px-3 py-2 text-left text-body-sm hover:bg-surface-2 ${
              isPicked ? "bg-accent-soft text-accent" : "text-fg"
            }`}
          >
            <span className="min-w-0 flex-1">
              <span className="block truncate">{o.label}</span>
              {o.hint ? (
                <span className="block truncate text-caption text-fg-subtle">{o.hint}</span>
              ) : null}
            </span>
            {isPicked ? <Check size={16} className="shrink-0" /> : null}
          </button>
        );
      })}
    </div>
  ) : null;

  return (
    <>
      <button
        ref={anchor}
        type="button"
        disabled={disabled}
        onClick={toggle}
        aria-label={label}
        aria-expanded={open}
        className={controlBox(label, disabled, className)}
      >
        <ControlFace label={label} icon={<CaretDown size={16} />}>
          {picked?.label ?? <span className="text-fg-subtle">{placeholder}</span>}
        </ControlFace>
      </button>

      {panel ? createPortal(panel, document.body) : null}
    </>
  );
}
