import { STATIONS } from "./stations";

export const STEP_NAME: Record<number, string> = Object.fromEntries(
  STATIONS.map((s) => [s.no, s.name]),
);
