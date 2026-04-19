// Full-width banner: headline promise + current wallet balance on the right.
// Rolls the old WalletCard's info into the banner so nothing is lost.
import type { UserProfile, Wallet } from "../types";
import { formatRupees } from "../utils";

interface Props {
  profile: UserProfile | null;
  wallet: Wallet | null;
}

export default function TomorrowDebit({ profile, wallet }: Props) {
  if (!profile || profile.active_loans.length === 0) {
    return null;
  }

  const total = profile.total_daily_commitment;
  const count = profile.active_loans.length;

  return (
    <div className="flex items-center justify-between rounded-2xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-5 shadow-sm">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">
          Tomorrow&apos;s auto-debit
        </div>
        <div className="mt-1 flex items-baseline gap-3">
          <span className="text-3xl font-bold text-blue-900 tabular-nums">
            {formatRupees(total)}
          </span>
          <span className="text-sm text-blue-800">
            from your wallet &mdash; runs automatically
          </span>
        </div>
        <div className="mt-1 text-xs text-blue-700">
          across {count} active loan{count === 1 ? "" : "s"} &middot; no action needed
        </div>
      </div>

      <div className="text-right">
        <div className="text-[11px] font-semibold uppercase tracking-wide text-blue-700">
          Wallet balance
        </div>
        <div className="mt-0.5 text-2xl font-bold text-blue-900 tabular-nums">
          {wallet ? formatRupees(wallet.balance) : "\u2014"}
        </div>
      </div>
    </div>
  );
}
