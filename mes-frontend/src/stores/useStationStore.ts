import { create } from "zustand";
import { persist } from "zustand/middleware";

type StationState = {
  picked: number | null;
  setPicked: (station: number | null) => void;
};

export const useStationStore = create<StationState>()(
  persist(
    (set) => ({
      picked: null,
      setPicked: (picked) => set({ picked }),
    }),
    { name: "mes-station" },
  ),
);
