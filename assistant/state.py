"""Shared LangGraph state for the assistant.

Every node reads from AssistantState and returns a partial dict that LangGraph
merges back in. Keep money fields as strings (not Decimal) so the state is
cleanly JSON-serialisable for tracing.

Semantics:
- Most fields: replace on update (default LangGraph behaviour).
- node_trail: append via Annotated[..., operator.add] so every node that runs
  contributes its name to the trace without overwriting earlier entries.
"""
import operator
from typing import Annotated, Literal, TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class Chunk(TypedDict):
    text: str
    source: str      # e.g. "policy/daily-debit.md"
    score: float     # cosine similarity, higher is better


class DBContext(TypedDict, total=False):
    loan_id: int
    amount: str
    daily_repayment: str
    avg_daily_income: str
    daily_expenses: str
    duration_days: int
    status: str
    is_sustainable: bool
    wallet_balance: str
    risk_level: str | None
    risk_reasons: list[str]
    buffer_days: float | None


class JudgeVerdict(TypedDict):
    relevance: float
    groundedness: float
    completeness: float
    verdict: Literal["keep", "fallback"]
    reasoning: str


class AssistantState(TypedDict, total=False):
    # Inputs (set once by the API layer)
    query: str
    session_id: str
    loan_id: int | None

    # Progressive state, populated by nodes in order
    history: list[Message]
    rewritten_query: str
    db_context: DBContext | None
    user_profile: dict | None
    is_personal: bool
    retrieved_chunks: list[Chunk]
    rag_answer: str
    judge_verdict: JudgeVerdict
    used_fallback: bool

    # Output
    final_answer: str

    # Debug trace — appended by each node that runs
    node_trail: Annotated[list[str], operator.add]
