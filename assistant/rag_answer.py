"""NODE RESPONSIBILITY
Produce the first-pass answer using the user's query, their DB context (if
any), and the retrieved knowledge chunks. Picks the personal or general
system prompt based on is_personal.

Reads:  rewritten_query, db_context, is_personal, retrieved_chunks
Writes: rag_answer
Calls:  OpenAI (answer_model)
"""
import json

from openai import OpenAI

from assistant.guidelines import GENERAL_SYSTEM_PROMPT, PERSONAL_SYSTEM_PROMPT
from assistant.settings import get_settings
from assistant.state import AssistantState


def _build_prompt(state: AssistantState) -> tuple[str, str]:
    is_personal = bool(state.get("is_personal"))
    system = PERSONAL_SYSTEM_PROMPT if is_personal else GENERAL_SYSTEM_PROMPT

    query = state.get("rewritten_query") or state["query"]
    parts = [f"Question: {query}"]

    # User's full profile is always available. Include it so the assistant
    # can reference total commitments, history, outstanding across all loans.
    profile = state.get("user_profile")
    if profile:
        parts.append(
            "\nUser's overall financial profile:\n"
            + json.dumps(profile, indent=2, default=str)
        )

    # Specific loan focus (when loan_id is provided by the caller).
    if state.get("db_context"):
        ctx_json = json.dumps(state["db_context"], indent=2, default=str)
        parts.append(f"\nCurrently selected loan:\n{ctx_json}")

    chunks = state.get("retrieved_chunks") or []
    if chunks:
        chunks_text = "\n\n".join(
            f"[{i + 1}] Source: {c['source']}\n{c['text']}"
            for i, c in enumerate(chunks)
        )
        parts.append(f"\nRetrieved knowledge:\n{chunks_text}")

    return system, "\n".join(parts)


def run(state: AssistantState) -> dict:
    settings = get_settings()
    system, user_prompt = _build_prompt(state)

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.answer_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    answer = (response.choices[0].message.content or "").strip()
    return {
        "rag_answer": answer,
        "node_trail": ["rag_answer"],
    }
