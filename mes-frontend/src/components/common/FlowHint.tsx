import { ArrowRight, Warning } from "@/components/common/PhosphorIcons";
import { flowOf } from "@/constants/flow";

export function FlowHint({ station }: { station: number }) {
  const flow = flowOf(station);
  if (!flow) return null;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-body-sm">
        <span className="text-fg-subtle">{flow.from}</span>
        <ArrowRight size={18} className="text-fg-subtle" />
        <span className="font-medium text-fg">{flow.here}</span>
        <ArrowRight size={18} className="text-fg-subtle" />
        <span className="text-fg-subtle">{flow.next}</span>
      </div>
      {flow.back ? (
        <p className="flex items-center gap-2 text-body-sm text-warn">
          <Warning size={18} weight="fill" />
          {flow.back}
        </p>
      ) : null}
    </div>
  );
}
