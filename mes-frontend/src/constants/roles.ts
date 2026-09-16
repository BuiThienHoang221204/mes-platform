/**
 * Bảng quyền BRD §9b — chép từ `app/common/security/permissions.py`.
 *
 * R21 — Ẩn/hiện theo quyền chỉ để ĐỠ BẤM NHẦM. Backend vẫn chặn bằng
 * `require_step`. Đừng bao giờ nghĩ "FE ẩn rồi thì khỏi cần".
 */
export const FULL = "FULL";
export const VIEW = "VIEW";
export type Perm = typeof FULL | typeof VIEW | null;

export const PLANNER = "PLANNER";

/** phòng ban → { trạm: mức quyền } */
const DEPT_PERM: Record<string, Record<number, Perm>> = {
  WAREHOUSE_OUT: { 0: FULL, 4: VIEW },
  SETUP: { 1: FULL, 4: VIEW },
  QC: { 2: FULL, 4: VIEW },
  WAITING: { 3: FULL, 4: FULL },   // §9b.4 — ngoại lệ DUY NHẤT
  PRODUCTION: { 4: FULL },
  WAREHOUSE_IN: { 5: FULL, 4: VIEW },
};

const deptOf = (role: string): string | null => {
  const m = /^(.*)_(LEADER|MEMBER)$/.exec(role);
  return m ? m[1] : null;
};

/** Mức cao nhất trong các vai — một người giữ được nhiều vai. */
export function permissionFor(roles: string[], step: number): Perm {
  if (roles.includes(PLANNER)) return FULL;
  let best: Perm = null;
  for (const r of roles) {
    const d = deptOf(r);
    if (!d) continue;
    const lv = DEPT_PERM[d]?.[step];
    if (lv === FULL) return FULL;
    if (lv === VIEW) best = VIEW;
  }
  return best;
}

/** Trạm mà người này THAO TÁC được — dùng để đoán trạm mặc định khi đăng nhập. */
export function ownStations(roles: string[]): number[] {
  return [0, 1, 2, 3, 4, 5].filter((s) => permissionFor(roles, s) === FULL);
}
