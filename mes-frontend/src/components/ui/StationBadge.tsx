import { stationName } from "@/constants/stations";

type Props = {
  station: number;
  size?: "sm" | "md";
  nameOnly?: boolean;
  muted?: boolean;
};

export function StationBadge({ station, size = "md", nameOnly, muted }: Props) {
  const box = size === "sm" ? "h-7 w-7 text-body-sm" : "h-9 w-9 text-body-lg";
  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap">
      <span
        className={`flex shrink-0 items-center justify-center rounded-pill tnum ${box} ${
          muted ? "bg-surface-2 text-fg-muted" : "bg-accent text-accent-on"
        }`}
      >
        {station}
      </span>
      {nameOnly === false ? null : (
        <span className={size === "sm" ? "text-body-sm" : "text-body"}>{stationName(station)}</span>
      )}
    </span>
  );
}
