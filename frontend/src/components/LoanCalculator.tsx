import { useState } from "react";
import Card from "./Card";
import { api } from "../api";
import { formatRupees } from "../utils";
import type {
  EligibilityResponse,
  RepaymentType,
  UserProfile,
} from "../types";

interface Props {
  profile: UserProfile | null;
  dailyIncome: string;
  onLoanCreated?: () => void;
}

export default function LoanCalculator({
  profile,
  dailyIncome,
  onLoanCreated,
}: Props) {
  const [amount, setAmount] = useState<string>("5000");
  const [duration, setDuration] = useState<string>("60");
  const [interestPct, setInterestPct] = useState<string>("5");
  const [repaymentType, setRepaymentType] =
    useState<RepaymentType>("fixed_daily");
  const [pctOfIncome, setPctOfIncome] = useState<string>("20");

  const [result, setResult] = useState<EligibilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [applying, setApplying] = useState(false);
  const [appliedMsg, setAppliedMsg] = useState<string | null>(null);

  function currentIncome(): number {
    const parsed = parseFloat(dailyIncome);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 1000;
  }

  function buildParams() {
    return {
      amount: parseFloat(amount),
      duration_days: parseInt(duration, 10),
      interest_rate: parseFloat(interestPct) / 100,
      repayment_type: repaymentType,
      repayment_percentage:
        repaymentType === "income_linked"
          ? parseFloat(pctOfIncome) / 100
          : null,
      avg_daily_income: currentIncome(),
    };
  }

  async function check() {
    setError(null);
    setAppliedMsg(null);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.checkEligibility(buildParams());
      setResult(res);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function applyForLoan() {
    if (!profile || !profile.wallet_id) {
      setError("No wallet on file. Cannot create loan.");
      return;
    }
    setApplying(true);
    setError(null);
    try {
      const params = buildParams();
      await api.createLoan({
        wallet_id: profile.wallet_id,
        amount: params.amount,
        duration_days: params.duration_days,
        interest_rate: params.interest_rate,
        avg_daily_income: currentIncome(),
        repayment_type: params.repayment_type,
        repayment_percentage: params.repayment_percentage,
      });
      setAppliedMsg(
        `Loan created for ${formatRupees(parseFloat(amount))}. Auto-debit starts tomorrow.`
      );
      setResult(null);
      onLoanCreated?.();
    } catch (e) {
      setError(String(e));
    } finally {
      setApplying(false);
    }
  }

  return (
    <Card title="Loan Calculator" subtitle="check eligibility for a new loan">
      <div className="space-y-3 text-sm">
        <Field
          label="Amount (Rs)"
          value={amount}
          onChange={setAmount}
          type="number"
        />
        <Field
          label="Duration (days)"
          value={duration}
          onChange={setDuration}
          type="number"
        />
        <Field
          label="Interest rate (%)"
          value={interestPct}
          onChange={setInterestPct}
          type="number"
        />

        <div>
          <label className="mb-1 block text-xs uppercase tracking-wide text-slate-500">
            Repayment type
          </label>
          <div className="flex gap-2">
            <TypeOption
              label="Fixed daily"
              selected={repaymentType === "fixed_daily"}
              onClick={() => setRepaymentType("fixed_daily")}
            />
            <TypeOption
              label="% of daily income"
              selected={repaymentType === "income_linked"}
              onClick={() => setRepaymentType("income_linked")}
            />
          </div>
        </div>

        {repaymentType === "income_linked" && (
          <Field
            label="Percentage of daily income (%)"
            value={pctOfIncome}
            onChange={setPctOfIncome}
            type="number"
          />
        )}

        <button
          onClick={check}
          disabled={loading || applying}
          className="w-full rounded-lg bg-slate-900 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
        >
          {loading ? "Checking..." : "Check eligibility"}
        </button>

        {error && (
          <div className="rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-800">
            {error}
          </div>
        )}

        {appliedMsg && (
          <div className="rounded border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-800">
            {appliedMsg}
          </div>
        )}

        {result && (
          <ResultPanel
            result={result}
            canApply={result.eligible && !!profile?.wallet_id}
            applying={applying}
            onApply={applyForLoan}
          />
        )}
      </div>
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="mb-1 block text-xs uppercase tracking-wide text-slate-500">
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border border-slate-300 bg-white px-3 py-1.5 text-sm outline-none focus:border-slate-500"
      />
    </div>
  );
}

function TypeOption({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-1 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
        selected
          ? "border-slate-900 bg-slate-900 text-white"
          : "border-slate-300 bg-white text-slate-700 hover:border-slate-500"
      }`}
    >
      {label}
    </button>
  );
}

function ResultPanel({
  result,
  canApply,
  applying,
  onApply,
}: {
  result: EligibilityResponse;
  canApply: boolean;
  applying: boolean;
  onApply: () => void;
}) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        result.eligible
          ? "border-emerald-300 bg-emerald-50"
          : "border-rose-300 bg-rose-50"
      }`}
    >
      <div className="flex items-center justify-between">
        <span
          className={`text-sm font-semibold ${
            result.eligible ? "text-emerald-800" : "text-rose-800"
          }`}
        >
          {result.eligible ? "\u2713 Eligible" : "\u2717 Not eligible"}
        </span>
        <span className="text-xs text-slate-600">
          Daily: {formatRupees(result.proposed_daily_repayment)}
        </span>
      </div>

      <div className="mt-3 space-y-1.5 text-xs">
        {result.rules.map((r) => (
          <div key={r.name} className="flex gap-2">
            <span className={r.passed ? "text-emerald-600" : "text-rose-600"}>
              {r.passed ? "\u2713" : "\u2717"}
            </span>
            <span className="text-slate-700">
              <span className="font-medium">{r.name.replace(/_/g, " ")}:</span>{" "}
              {r.detail}
            </span>
          </div>
        ))}
      </div>

      {!result.eligible && parseFloat(result.suggested_max_amount) > 0 && (
        <div className="mt-3 border-t border-slate-200 pt-2 text-xs text-slate-700">
          <span className="font-medium">Suggested max you could take:</span>{" "}
          {formatRupees(result.suggested_max_amount)}
        </div>
      )}
      {!result.eligible && parseFloat(result.suggested_max_amount) === 0 && (
        <div className="mt-3 border-t border-slate-200 pt-2 text-xs text-slate-700">
          Your current commitments leave no room for a new loan right now.
        </div>
      )}

      {canApply && (
        <button
          onClick={onApply}
          disabled={applying}
          className="mt-3 w-full rounded-lg bg-emerald-600 py-2 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-50"
        >
          {applying ? "Creating loan..." : "Apply now - create this loan"}
        </button>
      )}
    </div>
  );
}
