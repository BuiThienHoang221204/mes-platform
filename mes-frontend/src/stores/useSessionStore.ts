import { create } from "zustand";

/**
 * KHÔNG persist — quyền phải hỏi lại server mỗi lần mở app (FE-PLAN §4.2).
 * Đây là DANH TÍNH, không phải dữ liệu nghiệp vụ, nên nó được ở Zustand.
 */
type SessionState = {
  fullName: string | null;
  roles: string[];
  checked: boolean;                    // đã gọi /auth/refresh lần đầu chưa
  setSession: (fullName: string, roles: string[]) => void;
  clear: () => void;
  markChecked: () => void;
};

export const useSessionStore = create<SessionState>((set) => ({
  fullName: null,
  roles: [],
  checked: false,
  setSession: (fullName, roles) => set({ fullName, roles, checked: true }),
  clear: () => set({ fullName: null, roles: [], checked: true }),
  markChecked: () => set({ checked: true }),
}));
