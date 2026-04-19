// Shapes returned by the FastAPI backend. Decimals come over as strings.

export interface Wallet {
  id: number;
  user_id: string;
  balance: string;
  created_at: string;
}

export type RepaymentType = "fixed_daily" | "income_linked";

export interface LoanTerms {
  total_payable: string;
  base_daily: string;
  safe_daily: string;
  recommended_daily: string;
  is_sustainable: boolean;
  reason: string | null;
  repayment_type: string;
  repayment_percentage: string | null;
}

export interface Loan {
  id: number;
  user_id: string;
  wallet_id: number;
  amount: string;
  duration_days: number;
  interest_rate: string;
  daily_repayment: string;
  repayment_type: RepaymentType;
  repayment_percentage: string | null;
  income_type: string;
  avg_daily_income: string;
  daily_expenses: string;
  status: string;
  start_date: string;
  created_at: string;
}

export interface LoanDetail {
  loan: Loan;
  terms: LoanTerms;
}

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface RiskScore {
  loan_id: number;
  risk_level: RiskLevel;
  reasons: string[];
  suggested_action: string;
  buffer_days: number;
  skip_count: number;
  debit_count: number;
  is_sustainable: boolean;
}

export interface AskResponse {
  answer: string;
  session_id: string;
  sources: string[];
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

// Profile + eligibility + portfolio risk (the surfaces the UI actually uses)

export interface LoanStats {
  id: number;
  amount: string;
  daily_repayment: string;
  repayment_type: RepaymentType;
  repayment_percentage: string | null;
  duration_days: number;
  status: string;
  is_sustainable: boolean;
  avg_daily_income: string;
  paid: string;
  outstanding: string;
  debit_attempts: number;
  skip_count: number;
  skip_rate: number;
}

export interface UserProfile {
  user_id: string;
  wallet_id: number | null;
  wallet_balance: string;
  active_loans: LoanStats[];
  closed_loans: LoanStats[];
  total_daily_commitment: string;
  total_outstanding: string;
  total_debits: number;
  total_skips: number;
  overall_skip_rate: number;
  avg_daily_income: string;
  has_defaulted_loan: boolean;
}

export interface EligibilityRequest {
  user_id?: string;
  amount: number;
  duration_days: number;
  interest_rate: number;
  repayment_type: RepaymentType;
  repayment_percentage?: number | null;
  avg_daily_income?: number | null;
}

export interface EligibilityRule {
  name: string;
  passed: boolean;
  detail: string;
}

export interface EligibilityResponse {
  eligible: boolean;
  rules: EligibilityRule[];
  reasons_fail: string[];
  proposed_daily_repayment: string;
  proposed_total_payable: string;
  suggested_max_amount: string;
}

export interface LoanCreateRequest {
  wallet_id: number;
  amount: number;
  duration_days: number;
  interest_rate: number;
  income_type?: string;
  avg_daily_income: number;
  daily_expenses?: number;
  repayment_type: RepaymentType;
  repayment_percentage?: number | null;
  user_id?: string;
}

export interface LoanCreateResponse {
  loan: Loan;
  terms: LoanTerms;
  simulation_run_id: number;
}

export interface PortfolioRisk {
  user_id: string;
  risk_level: RiskLevel;
  reasons: string[];
  suggested_action: string;
  avg_daily_income: string;
  safe_daily_cap: string;
  total_daily_commitment: string;
  buffer_days: number;
  total_debits: number;
  total_skips: number;
  is_sustainable: boolean;
}
