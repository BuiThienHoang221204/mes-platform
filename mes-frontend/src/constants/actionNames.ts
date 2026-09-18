/**
 * Chép từ `mes-backend/app/common/vocab/action_codes.py`.
 *
 * Nhật ký là màn hình người vận hành và quản lý đọc để truy ra chuyện gì đã xảy
 * ra, nên nó phải nói tiếng Việt. `PACK_COMPLETE` hay `STEP4_FINISH_ALL` là tên
 * hằng số cho lập trình viên — bắt người đứng máy dịch chúng là đẩy việc của máy
 * sang cho người.
 *
 * Mã vẫn giữ trong `title` của ô: khi cần đối chiếu với log server hay báo lỗi
 * thì vẫn tra được, chỉ là không chiếm chỗ của câu tiếng Việt.
 *
 * `tone` chia theo NGHĨA chứ không theo trạm: dòng nào đóng một mốc thì xanh,
 * dòng nào là sự cố hay quay lui thì đỏ, còn lại để trung tính. Liếc một cái là
 * thấy ngay chỗ nào vòng bị trả về.
 */
import type { PillTone } from "@/constants/status";

type ActionMeta = { label: string; tone: PillTone };

export const ACTION_META: Record<string, ActionMeta> = {
  // Vòng đời một lệnh
  MO_CREATE: { label: "Tạo lệnh", tone: "flat" },
  MO_SUBMIT: { label: "Chốt lệnh", tone: "accent" },
  MO_CANCEL: { label: "Huỷ lệnh", tone: "danger" },
  MO_PARTIAL: { label: "Nhập kho thiếu — còn phần dư", tone: "warn" },
  MO_COMPLETE: { label: "Đủ số, đóng đơn", tone: "ok" },

  // Vòng chạy
  ROUND_OPEN: { label: "Mở vòng mới", tone: "accent" },
  RETURN_KHO: { label: "Trả về Kho xuất", tone: "danger" },
  RETURN_BANCHO: { label: "Trả về Bàn team leader", tone: "warn" },

  // Quét nhận sáu trạm
  STEP0_ACCEPT: { label: "Kho xuất nhận", tone: "accent" },
  STEP1_ACCEPT: { label: "Setup máy nhận", tone: "accent" },
  STEP2_ACCEPT: { label: "QC nhận", tone: "accent" },
  STEP3_ACCEPT: { label: "Bàn team leader nhận", tone: "accent" },
  STEP4_ACCEPT: { label: "Sản xuất nhận", tone: "accent" },
  STEP5_ACCEPT: { label: "Kho nhập nhận", tone: "accent" },

  // Trạm 0
  KHO_HANDOVER: { label: "Bàn giao vật tư xuống Setup", tone: "flat" },

  // Trạm 2
  QC_PASS: { label: "QC đạt", tone: "ok" },
  QC_FAIL: { label: "QC không đạt", tone: "danger" },

  // Trạm 4 — chuyền
  RUN_ADD: { label: "Thêm chuyền", tone: "flat" },
  RUN_START: { label: "Chuyền vào Đang lắp ráp", tone: "ok" },
  RUN_HOLD: { label: "Dừng chuyền", tone: "danger" },
  HOURLY_ADD: { label: "Ghi sản lượng giờ", tone: "flat" },
  STEP4_FINISH_ALL: { label: "Chốt sổ sản xuất", tone: "ok" },

  // Trạm 4 — đóng thùng
  PACK_START: { label: "Mở sổ đóng thùng", tone: "flat" },
  PACK_HOURLY: { label: "Ghi thùng theo giờ", tone: "flat" },
  PACK_COMPLETE: { label: "Kết thúc đóng thùng", tone: "ok" },
};

/** Mã lạ vẫn hiện được — nhật ký không xoá được nên không giấu dòng nào. */
export const actionMeta = (code: string): ActionMeta =>
  ACTION_META[code] ?? { label: code, tone: "flat" };
