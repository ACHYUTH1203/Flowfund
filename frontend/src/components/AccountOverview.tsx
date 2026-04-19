// Shows the user's full account at a glance: totals + per-loan stats.
import Card from "./Card";
import { formatRupees } from "../utils";
import type { UserProfile } from "../types";

interface Props {
  profile: UserProfile | null;
  selectedLoanId: number;
  onSelect: (id: number) => void;
}

export default function AccountOverview({
  profile,
  selectedLoanId,
  onSelect,
}: Props) {
  if (!profile) {
    return (
      <Card title="My Loans">
        <div className="text-slate-400">loading...</div>
      </Card>
    );
  }

  const reliability = (1 - profile.overall_skip_rate) * 100;
  const reliabilityTone: "good" | "bad" =
    profile.total_debits === 0 || reliability >= 80 ? "good" : "bad";

  return (
    <Card title="My Loans" subtitle="track record across all loans">
      <div className="mb-4 grid grid-cols-2 gap-3 text-sm">
        <Stat label="Active loans" value={String(profile.active_loans.length)} />
        <Stat label="Total outstanding" value={formatRupees(profile.total_outstanding)} />
        <Stat label="Daily commitment" value={formatRupees(profile.total_daily_commitment)} />
        <Stat
          label="Reliability"
          value={
            profile.total_debits === 0
              ? "—"
              : `${reliability.toFixed(0)}%`
          }
          tone={reliabilityTone}
        />
      </div>

      <div className="space-y-2">
        {profile.active_loans.map((l) => {
          const progressPct =
            parseFloat(l.paid) + parseFloat(l.outstanding) > 0
              ? (parseFloat(l.paid) /
                  (parseFloat(l.paid) + parseFloat(l.outstanding))) *
                100
              : 0;
          const loanReliability = (1 - l.skip_rate) * 100;
          const successfulDebits = l.debit_attempts - l.skip_count;
          const typeLabel =
            l.repayment_type === "income_linked"
              ? `income-linked @${l.repayment_percentage ? (parseFloat(l.repayment_percentage) * 100).toFixed(0) : "-"}%`
              : "fixed daily";
          const selected = l.id === selectedLoanId;

          return (
            <button
              key={l.id}
              onClick={() => onSelect(l.id)}
              className={`w-full rounded-lg border p-3 text-left text-xs transition ${
                selected
                  ? "border-slate-900 bg-slate-50"
                  : "border-slate-200 bg-white hover:border-slate-400"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900">
                  Loan #{l.id}
                </span>
                <span className="text-[10px] uppercase tracking-wide text-slate-500">
                  {typeLabel}
                </span>
              </div>
              <div className="mt-1 flex items-center justify-between text-slate-600">
                <span>{formatRupees(l.amount)}</span>
                <span>daily {formatRupees(l.daily_repayment)}</span>
              </div>

              <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full bg-emerald-500 transition-all"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
              <div className="mt-1 flex justify-between text-[10px] text-slate-500">
                <span>paid {formatRupees(l.paid)}</span>
                <span>outstanding {formatRupees(l.outstanding)}</span>
              </div>

              <div className="mt-2 flex justify-between text-[10px]">
                <span className={l.is_sustainable ? "text-emerald-600" : "text-rose-600"}>
                  {l.is_sustainable ? "sustainable" : "unsustainable"}
                </span>
                <span
                  className={
                    l.debit_attempts > 0 && l.skip_rate >= 0.2
                      ? "text-rose-600"
                      : "text-emerald-600"
                  }
                >
                  {l.debit_attempts === 0
                    ? "no debits yet"
                    : `${successfulDebits}/${l.debit_attempts} successful (${loanReliability.toFixed(0)}%)`}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </Card>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "good" | "bad";
}) {
  const toneClass =
    tone === "bad"
      ? "text-rose-700"
      : tone === "good"
      ? "text-emerald-700"
      : "text-slate-900";
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className={`font-semibold tabular-nums ${toneClass}`}>{value}</div>
    </div>
  );
}
