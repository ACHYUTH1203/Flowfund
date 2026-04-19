import type {
  AskResponse,
  EligibilityRequest,
  EligibilityResponse,
  LoanCreateRequest,
  LoanCreateResponse,
  LoanDetail,
  PortfolioRisk,
  RiskScore,
  UserProfile,
  Wallet,
} from "./types";

// Empty base = same-origin. In dev, Vite's proxy (see vite.config.ts) forwards
// /wallets, /loans, /users, /ask, /health to the backend on port 8000. In
// production, FastAPI serves the built frontend and the API from one origin.
const BASE = "";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  getWallet: (id: number) => get<Wallet>(`/wallets/${id}`),
  getLoan: (id: number) => get<LoanDetail>(`/loans/${id}`),
  getRiskScore: (id: number) => get<RiskScore>(`/loans/${id}/risk-score`),
  ask: (body: { query: string; session_id: string; loan_id?: number | null }) =>
    post<AskResponse>(`/ask`, body),
  getProfile: (userId: string) => get<UserProfile>(`/users/${userId}/profile`),
  checkEligibility: (body: EligibilityRequest) =>
    post<EligibilityResponse>(`/loans/eligibility`, body),
  createLoan: (body: LoanCreateRequest) =>
    post<LoanCreateResponse>(`/loans`, body),
  getPortfolioRisk: (userId: string) =>
    get<PortfolioRisk>(`/users/${userId}/portfolio-risk`),
};
