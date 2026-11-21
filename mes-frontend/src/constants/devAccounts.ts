export type DevAccount = {
  emp: string;
  name: string;
  dept: string;
  level: string;
  station: number | null;
};

export const DEV_PIN = "1234";

export const DEV_ACCOUNTS: DevAccount[] = [
  { emp: "NV010", name: "Lấy nguyên liệu A", dept: "Lấy nguyên liệu", level: "Thành viên", station: 0 },
  { emp: "NV020", name: "Setup A", dept: "Setup máy", level: "Thành viên", station: 1 },
  { emp: "NV040", name: "Team Leader", dept: "Team Leader", level: "Thành viên", station: 2 },
  { emp: "NV050", name: "Leader L1", dept: "Sản xuất", level: "Tổ trưởng", station: 3 },
  { emp: "NV060", name: "Đóng gói", dept: "Sản xuất", level: "Thành viên", station: 3 },
  { emp: "NV070", name: "Kho nhập A", dept: "Kho nhập", level: "Thành viên", station: 4 },
];

export const DEV_PLANNER: DevAccount = {
  emp: "NV001",
  name: "Planner A",
  dept: "Planner",
  level: "Điều độ",
  station: null,
};

export const IS_DEV = true;
