type Props = {
  round: number;
  target?: number;
  quantity?: number;
};

export function RoundBadge({ round, target, quantity }: Props) {
  const first = round <= 1;
  const partial = target != null && quantity != null && target < quantity;

  return (
    <span className="inline-flex items-center gap-2 whitespace-nowrap">
      <span
        className={`rounded-pill px-3 py-1 text-badge ${
          first ? "bg-surface-2 text-fg-muted" : "bg-warn-soft text-warn"
        }`}
      >
        Vòng {round}
      </span>
      {partial ? (
        <span className="text-caption tnum text-fg-muted">
          {target.toLocaleString("vi-VN")}/{quantity.toLocaleString("vi-VN")}
        </span>
      ) : null}
    </span>
  );
}
