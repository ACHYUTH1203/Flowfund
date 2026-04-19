// Editable daily-income input. Drives the Loan Calculator's 30% rule check.
// Default value is kept in the constant DEFAULT_DAILY_INCOME so the demo
// starts in a sensible state and the user can freely override.
import Card from "./Card";

export const DEFAULT_DAILY_INCOME = "1000";

interface Props {
  value: string;
  onChange: (v: string) => void;
}

export default function IncomeCard({ value, onChange }: Props) {
  return (
    <Card
      title="Your Daily Income"
      subtitle="drives the 30% affordability rule"
    >
      <div className="relative">
        <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-2xl font-semibold text-slate-500">
          &#8377;
        </span>
        <input
          type="number"
          min="0"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={DEFAULT_DAILY_INCOME}
          className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-10 pr-3 text-3xl font-bold tabular-nums text-slate-900 outline-none focus:border-slate-500"
        />
      </div>
      <div className="mt-2 text-xs text-slate-500">
        change this to test different income scenarios
      </div>
    </Card>
  );
}
