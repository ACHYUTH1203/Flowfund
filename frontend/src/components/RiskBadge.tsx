import Card from "./Card";
import type { PortfolioRisk } from "../types";

interface Props {
  risk: PortfolioRisk | null;
}

const STYLES = {
  LOW: "bg-emerald-100 text-emerald-800 ring-emerald-300",
  MEDIUM: "bg-amber-100 text-amber-800 ring-amber-300",
  HIGH: "bg-rose-100 text-rose-800 ring-rose-300",
};

export default function RiskBadge({ risk }: Props) {
  if (!risk) {
    return (
      <Card title="Payment Health" subtitle="how your loans are tracking">
        <div className="text-slate-400">loading...</div>
      </Card>
    );
  }

  const badge = STYLES[risk.risk_level];

  return (
    <Card title="Payment Health" subtitle="how your loans are tracking">
      <div
        className={`inline-flex rounded-full px-3 py-1 text-sm font-semibold ring-1 ${badge}`}
      >
        {risk.risk_level}
      </div>

      {risk.reasons.length > 0 && (
        <ul className="mt-3 space-y-1 text-xs text-slate-600">
          {risk.reasons.slice(0, 2).map((r, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-slate-400">•</span>
              <span>{r}</span>
            </li>
          ))}
        </ul>
      )}

      {risk.suggested_action && (
        <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-700">
          <span className="font-medium">Action: </span>
          {risk.suggested_action}
        </div>
      )}
    </Card>
  );
}
