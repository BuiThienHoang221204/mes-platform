"use client";

/**
 * R18 — CỬA DUY NHẤT cho icon. Cấm SVG inline, cấm import
 * `@phosphor-icons/react` ở bất kỳ tệp nào khác.
 *
 * Lý do không phải thẩm mỹ: cần icon mới thì người sau phải biết tìm ở đâu, và
 * trộn hai bộ là hai phong cách nét trên cùng một màn hình. Thêm icon = thêm
 * một dòng export ở dưới, tra tên tại phosphoricons.com.
 *
 * CHÚ Ý — Phosphor KHÔNG có prop `strokeWidth`. Truyền vào thì không báo lỗi mà
 * cũng không có tác dụng: icon vẫn mảnh trong khi mình tưởng đã làm đậm. Muốn
 * đậm thì `weight="bold"`, muốn to thì `size={28}` hoặc `className="h-7 w-7"`.
 */

import { IconContext } from "@phosphor-icons/react";
import type { ReactNode } from "react";

export {
  // quét & trạm
  QrCode, Scan, Camera, Barcode,
  // kho & hàng
  Package, Truck, Warehouse, Stack, Cube,
  // trạm / công đoạn
  Wrench, MagnifyingGlass, ClipboardText, Gear, Factory,
  // kết quả
  CheckCircle, XCircle, Warning, WarningCircle, Info, SealCheck,
  // điều khiển chuyền
  Play, Pause, StopCircle, ArrowsClockwise,
  // thời gian & số liệu
  Clock, Timer, ChartBar, ListNumbers, Table,
  // điều hướng
  ArrowLeft, ArrowRight, CaretDown, CaretRight, CaretUp, List, X,
  // người & hệ thống
  User, UserSwitch, SignOut, SignIn, Lock, DeviceTablet,
  // khác
  Plus, Minus, Trash, Printer, DownloadSimple, UploadSimple,
  TextAa, Sun, Moon, Desktop,
} from "@phosphor-icons/react";

/**
 * Đặt weight/size mặc định MỘT chỗ, bọc quanh app trong `layout.tsx`.
 *
 * `size: 24` là mặc định cho xưởng — nét mảnh 16px thì người đeo găng đứng cách
 * màn nửa mét không nhìn ra. Icon trong nút thao tác chính tự nâng lên
 * `size={28} weight="bold"` tại chỗ dùng.
 */
export function IconProvider({ children }: { children: ReactNode }) {
  return (
    <IconContext.Provider value={{ size: 24, weight: "regular" }}>
      {children}
    </IconContext.Provider>
  );
}
