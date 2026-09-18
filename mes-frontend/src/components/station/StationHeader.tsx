import { FlowHint } from "@/components/common/FlowHint";
import { PageHeader } from "@/components/common/PageHeader";
import { stationName } from "@/constants/stations";

type Props = {
  station: number;
  title: string;
  children?: React.ReactNode;
};

export function StationHeader({ station, title, children }: Props) {
  return (
    <div className="mb-4 lg:mb-6">
      <PageHeader kicker={`Trạm ${station} · ${stationName(station)}`} title={title}>
        {children}
      </PageHeader>
      <FlowHint station={station} />
    </div>
  );
}
