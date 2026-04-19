import Card from "./Card";
import type { PortfolioRisk } from "../types";

interface Props {
  risk: PortfolioRisk | null;
}

function colourFor(days: number): { bar: string; label: string } {
  if (days < 1) return { bar: "bg-risk-high", label: "Critical" };
  if (days < 3) return { bar: "bg-risk-medium", label: "Thin" };
  return { bar: "bg-risk-low", label: "Healthy" };
}

export default function BufferGauge({ risk }: Props) {
  const days = risk?.buffer_days ?? 0;
  const clampedPct = Math.min(100, (days / 6) * 100);
  const { bar, label } = colourFor(days);

  return (
    <Card
      title="Wallet Buffer"
      subtitle="days of combined daily debits covered"
    >
      <div className="text-4xl font-bold text-slate-900 tabular-nums">
        {risk ? `${days.toFixed(1)}d` : "—"}
      </div>
      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
        <div
          className={`h-full rounded-full transition-all ${bar}`}
          style={{ width: `${clampedPct}%` }}
        />
      </div>
      <div className="mt-2 flex justify-between text-xs text-slate-500">
        <span>{label}</span>
        <span>target: 3d</span>
      </div>
    </Card>
  );
}
