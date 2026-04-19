import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type {
  LoanDetail,
  PortfolioRisk,
  UserProfile,
  Wallet,
} from "../types";
import AccountOverview from "./AccountOverview";
import BufferGauge from "./BufferGauge";
import ChatWidget from "./ChatWidget";
import IncomeCard, { DEFAULT_DAILY_INCOME } from "./IncomeCard";
import LoanCalculator from "./LoanCalculator";
import LoanProjection from "./LoanProjection";
import LoanSummary from "./LoanSummary";
import ReliabilityCard from "./ReliabilityCard";
import RiskBadge from "./RiskBadge";
import TomorrowDebit from "./TomorrowDebit";

const USER_ID = "demo_user";

export default function Dashboard() {
  const [selectedLoanId, setSelectedLoanId] = useState<number | null>(null);

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [portfolioRisk, setPortfolioRisk] = useState<PortfolioRisk | null>(null);
  const [detail, setDetail] = useState<LoanDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  // User-editable daily income. Defaults to the code constant but the user
  // can override at any time - drives the Loan Calculator's eligibility check.
  const [dailyIncome, setDailyIncome] = useState<string>(DEFAULT_DAILY_INCOME);

  const refreshPortfolio = useCallback(async () => {
    try {
      const [p, r] = await Promise.all([
        api.getProfile(USER_ID),
        api.getPortfolioRisk(USER_ID),
      ]);
      setProfile(p);
      setPortfolioRisk(r);
      if (p.wallet_id) {
        const w = await api.getWallet(p.wallet_id);
        setWallet(w);
      }
      // Seed the income input from the profile's declared value on first
      // load only - don't overwrite a user edit on a subsequent refresh.
      setDailyIncome((cur) =>
        cur === DEFAULT_DAILY_INCOME && p.avg_daily_income
          ? String(parseFloat(p.avg_daily_income))
          : cur
      );
      setSelectedLoanId((cur) => {
        if (cur != null && p.active_loans.some((l) => l.id === cur)) {
          return cur;
        }
        return p.active_loans[0]?.id ?? null;
      });
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refreshPortfolio();
  }, [refreshPortfolio]);

  useEffect(() => {
    if (selectedLoanId == null) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const d = await api.getLoan(selectedLoanId);
        if (!cancelled) setDetail(d);
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedLoanId]);

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <div className="text-lg font-bold text-slate-900">
              FlowFund
            </div>
            <div className="text-xs text-slate-500">
              Smart Daily Loan Engine
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-600">
            <span className="rounded-full bg-slate-100 px-3 py-1">
              Signed in: <span className="font-semibold">{USER_ID}</span>
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6">
        {error && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">
            {error}
          </div>
        )}

        <div className="grid grid-cols-12 gap-5">
          <div className="col-span-12 space-y-5 lg:col-span-4">
            <LoanCalculator
              profile={profile}
              dailyIncome={dailyIncome}
              onLoanCreated={refreshPortfolio}
            />
            <AccountOverview
              profile={profile}
              selectedLoanId={selectedLoanId ?? -1}
              onSelect={setSelectedLoanId}
            />
          </div>

          <div className="col-span-12 space-y-5 lg:col-span-8">
            <TomorrowDebit profile={profile} wallet={wallet} />

            <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <IncomeCard value={dailyIncome} onChange={setDailyIncome} />
              <BufferGauge risk={portfolioRisk} />
              <RiskBadge risk={portfolioRisk} />
              <ReliabilityCard profile={profile} />
            </section>

            <LoanProjection detail={detail} />

            <LoanSummary detail={detail} />
          </div>
        </div>
      </main>

      <ChatWidget loanId={selectedLoanId} />
    </div>
  );
}
