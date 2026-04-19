"""POST /ask — the assistant's HTTP surface.

Returns answer + session_id + sources (citations). Internal flags like
used_fallback stay inside state and are not surfaced. When the fallback
path runs, sources is empty (no chunks were used for that answer).
"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from assistant.main import run_assistant

router = APIRouter(tags=["assistant"])


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    session_id: str = Field(min_length=1, max_length=64)
    loan_id: int | None = None


class AskResponse(BaseModel):
    answer: str
    session_id: str
    sources: list[str] = []


@router.post("/ask", response_model=AskResponse)
def ask(payload: AskRequest) -> AskResponse:
    result = run_assistant(
        query=payload.query,
        session_id=payload.session_id,
        loan_id=payload.loan_id,
    )

    sources: list[str] = []
    if not result.get("used_fallback", False):
        for chunk in result.get("retrieved_chunks", []) or []:
            src = chunk.get("source")
            if src and src not in sources:
                sources.append(src)

    return AskResponse(
        answer=result.get("final_answer", ""),
        session_id=payload.session_id,
        sources=sources,
    )
