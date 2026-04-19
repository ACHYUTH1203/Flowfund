import Card from "./Card";
import { formatRupees } from "../utils";
import type { LoanDetail } from "../types";

interface Props {
  detail: LoanDetail | null;
}

export default function LoanSummary({ detail }: Props) {
  if (!detail) {
    return (
      <Card title="Loan Summary">
        <div className="text-slate-400">loading...</div>
      </Card>
    );
  }

  const { loan, terms } = detail;
  const sustainable = terms.is_sustainable;

  return (
    <Card title="Loan Summary" subtitle={`#${loan.id} \u00B7 ${loan.status}`} className="col-span-full">
      <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
        <Metric label="Amount" value={formatRupees(loan.amount)} />
        <Metric label="Duration" value={`${loan.duration_days}d`} />
        <Metric label="Daily Repayment" value={formatRupees(loan.daily_repayment)} />
        <Metric label="Total Payable" value={formatRupees(terms.total_payable)} />
        <Metric label="Avg Income/day" value={formatRupees(loan.avg_daily_income)} />
        <Metric label="Expenses/day" value={formatRupees(loan.daily_expenses)} />
        <Metric label="Base Daily" value={formatRupees(terms.base_daily)} />
        <Metric label="Safe Daily" value={formatRupees(terms.safe_daily)} />
      </div>

      <div className="mt-4 flex items-center gap-3 text-sm">
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ${
            sustainable
              ? "bg-emerald-100 text-emerald-800 ring-emerald-300"
              : "bg-rose-100 text-rose-800 ring-rose-300"
          }`}
        >
          {sustainable ? "Sustainable" : "Unsustainable"}
        </span>
        {terms.reason && (
          <span className="text-xs text-slate-600">{terms.reason}</span>
        )}
      </div>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="font-semibold text-slate-900 tabular-nums">{value}</div>
    </div>
  );
}
