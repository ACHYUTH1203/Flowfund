# ClickPe Lite — Smart Daily Loan Engine

A prototype that converts monthly loan burden into small daily debits from a digital wallet — built for small business owners who earn daily but get charged monthly by traditional lenders. Includes portfolio-level risk scoring, an eligibility calculator, and a RAG-based AI assistant grounded in the user's own financial history.

## What it does

- **Daily auto-debit model** — a tiny amount pulled from the wallet each day, no lump-sum EMI shock.
- **Two repayment types** — fixed daily amount, or income-linked (pay a % of whatever you earned that day).
- **30% rule, portfolio-wide** — a user's *total* daily loan commitment can never exceed 30% of their daily income. The eligibility calculator refuses loans that would cross this line.
- **Payment reliability counter** — successful-debit track record, positively framed.
- **AI assistant** — answers plain-language financial questions using the user's actual loan data + a curated knowledge base (RBI rules, product policies, common FAQs). Built with LangGraph and OpenAI.
- **30-day simulated history** — the seed script runs a realistic 30-day simulation (including a 4-day shop closure) so the demo opens with meaningful data.

## Tech stack

- **Backend**: FastAPI, SQLAlchemy, SQLite (swap to Postgres in prod), OpenAI Python SDK, FAISS
- **AI pipeline**: LangGraph (query rewriter → context fetch → retriever → LLM → judge → conditional fallback → persist turn)
- **Frontend**: React 18 + TypeScript + Vite + TailwindCSS + Recharts + lucide-react

## Project layout

```
.
├── app/                   FastAPI backend
│   ├── api/               routers: wallets, loans, users
│   ├── models/            SQLAlchemy models
│   ├── schemas/           Pydantic request/response shapes
│   ├── services/          loan_simulator, risk, eligibility, profile, wallet
│   └── main.py            app entry — mounts routers and the built frontend
├── assistant/             LangGraph chat assistant + RAG
│   ├── corpus/            knowledge base (policy/concepts/regulation/faq)
│   ├── state.py           shared TypedDict across graph nodes
│   ├── graph.py           wires nodes into a StateGraph
│   └── *.py               one file per node
├── frontend/              React + Vite + Tailwind
│   └── src/components/    Dashboard, LoanCalculator, ChatWidget, ...
├── scripts/
│   ├── seed_demo.py       wipes + seeds DB with a 30-day simulated history
│   └── seed_rag.py        builds the FAISS index from corpus/
├── tests/                 pytest suite (loan_simulator + risk)
├── pyproject.toml         Poetry-managed Python deps
└── .env.example           copy to .env and add your OPENAI_API_KEY
```

## Local quickstart

Requires Python 3.11+ and Node 20+.

```bash
# 1. Python deps
poetry install

# 2. Frontend deps
cd frontend && npm install && cd ..

# 3. Environment
cp .env.example .env
#    open .env and paste your OPENAI_API_KEY

# 4. Seed the demo state
poetry run python scripts/seed_demo.py
poetry run python scripts/seed_rag.py

# 5. Run both servers (two terminals)
#    Terminal 1:
poetry run uvicorn app.main:app --reload
#    Terminal 2:
cd frontend && npm run dev

# 6. Open http://127.0.0.1:5173/
```

The Vite dev server proxies API calls (`/wallets`, `/loans`, `/users`, `/ask`, `/health`) to the FastAPI backend on port 8000, so the same relative URLs work in dev and production.

## Tests

```bash
poetry run pytest
# 26 tests across loan_simulator and risk engines
```

## API endpoints (summary)

| Method | Path | Purpose |
|--------|------|---------|
| `GET`  | `/health` | Liveness + DB ping |
| `POST` | `/wallets` | Create a wallet |
| `GET`  | `/wallets/{id}` | Fetch a wallet |
| `POST` | `/wallets/{id}/add-funds` | Credit the wallet |
| `POST` | `/wallets/{id}/debit` | Debit the wallet (idempotent) |
| `GET`  | `/wallets/{id}/transactions` | Paginated history |
| `POST` | `/loans` | Create a loan |
| `GET`  | `/loans/{id}` | Fetch a loan + derived terms |
| `GET`  | `/loans/{id}/schedule` | Day-by-day projection |
| `GET`  | `/loans/{id}/risk-score` | Per-loan risk (legacy; UI uses portfolio) |
| `POST` | `/loans/eligibility` | Check if user can take a new loan |
| `GET`  | `/users/{user_id}/profile` | Consolidated user state |
| `GET`  | `/users/{user_id}/portfolio-risk` | Portfolio-wide risk score |
| `POST` | `/ask` | Chat with the AI assistant |

Interactive docs at `/docs` when the server is running.
