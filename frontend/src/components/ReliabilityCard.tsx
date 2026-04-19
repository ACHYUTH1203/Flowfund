// Positively-framed payment history. Shows reliability % (success / total),
// not skip rate. Matches the "good credit scores are created" claim.
import Card from "./Card";
import type { UserProfile } from "../types";

interface Props {
  profile: UserProfile | null;
}

function toneFor(reliability: number, total: number): string {
  if (total === 0) return "text-slate-400";
  if (reliability >= 95) return "text-emerald-600";
  if (reliability >= 80) return "text-amber-600";
  return "text-rose-600";
}

export default function ReliabilityCard({ profile }: Props) {
  if (!profile) {
    return (
      <Card title="Reliability" subtitle="your payment track record">
        <div className="text-slate-400">loading...</div>
      </Card>
    );
  }

  const total = profile.total_debits;
  const success = total - profile.total_skips;
  const pct = total > 0 ? (success / total) * 100 : 100;
  const tone = toneFor(pct, total);

  return (
    <Card title="Reliability" subtitle="your payment track record">
      <div className={`text-4xl font-bold tabular-nums ${tone}`}>
        {total > 0 ? `${pct.toFixed(0)}%` : "—"}
      </div>
      <div className="mt-2 text-xs text-slate-500">
        {total > 0
          ? `${success} of ${total} debits successful`
          : "no debits yet"}
      </div>
    </Card>
  );
}
