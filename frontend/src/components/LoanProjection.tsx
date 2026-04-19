// Borrower-facing view of the selected loan's journey to zero.
// Outstanding balance declines from total_payable to zero as daily debits run.
import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import Card from "./Card";
import type { LoanDetail } from "../types";
import { formatRupees } from "../utils";

type Row = {
  day: number;
  outstanding: number;
  paid: number;
};

function projectOutstanding(detail: LoanDetail): Row[] {
  const totalPayable = parseFloat(detail.terms.total_payable);
  const dailyRepayment = parseFloat(detail.loan.daily_repayment);
  const duration = detail.loan.duration_days;

  const rows: Row[] = [];
  for (let day = 0; day <= duration; day++) {
    const paid = Math.min(totalPayable, dailyRepayment * day);
    const outstanding = Math.max(0, totalPayable - paid);
    rows.push({ day, outstanding, paid });
  }
  return rows;
}

function daysToClose(detail: LoanDetail): number {
  const totalPayable = parseFloat(detail.terms.total_payable);
  const dailyRepayment = parseFloat(detail.loan.daily_repayment);
  if (dailyRepayment <= 0) return detail.loan.duration_days;
  return Math.ceil(totalPayable / dailyRepayment);
}

interface Props {
  detail: LoanDetail | null;
}

export default function LoanProjection({ detail }: Props) {
  if (!detail) {
    return (
      <Card title="Your Loan Journey" className="col-span-full">
        <div className="text-slate-400">loading...</div>
      </Card>
    );
  }

  const data = projectOutstanding(detail);
  const closeDay = daysToClose(detail);

  return (
    <Card
      title="Your Loan Journey"
      subtitle={`Loan #${detail.loan.id} \u00B7 reaches zero on day ${closeDay}`}
      className="col-span-full"
    >
      <div className="mb-4 grid grid-cols-3 gap-4 text-sm">
        <Stat
          label="Daily debit"
          value={formatRupees(detail.loan.daily_repayment)}
          tone="blue"
        />
        <Stat
          label="Total payable"
          value={formatRupees(detail.terms.total_payable)}
          tone="slate"
        />
        <Stat
          label="Fully paid in"
          value={`${closeDay} days`}
          tone="emerald"
        />
      </div>

      <div className="h-72 w-full">
        <ResponsiveContainer>
          <AreaChart
            data={data}
            margin={{ top: 8, right: 20, left: 0, bottom: 8 }}
          >
            <defs>
              <linearGradient id="outstandingGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#1d4ed8" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <XAxis
              dataKey="day"
              tick={{ fontSize: 11, fill: "#64748b" }}
              label={{
                value: "Day",
                position: "insideBottom",
                offset: -2,
                fontSize: 11,
                fill: "#64748b",
              }}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#64748b" }}
              tickFormatter={(v: number) => `\u20B9${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip
              formatter={(v: number) =>
                `\u20B9${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
              }
              labelFormatter={(l) => `Day ${l}`}
            />
            <Area
              type="monotone"
              dataKey="outstanding"
              stroke="#1d4ed8"
              strokeWidth={2.5}
              fill="url(#outstandingGradient)"
              name="Outstanding"
              isAnimationActive={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 text-xs text-slate-500">
        Pay Rs {detail.loan.daily_repayment} daily \u00B7 no lump-sum surprises \u00B7
        loan closes on day {closeDay}.
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
  tone: "blue" | "slate" | "emerald";
}) {
  const toneClass =
    tone === "blue"
      ? "text-blue-700"
      : tone === "emerald"
      ? "text-emerald-700"
      : "text-slate-900";
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className={`text-lg font-semibold tabular-nums ${toneClass}`}>
        {value}
      </div>
    </div>
  );
}
