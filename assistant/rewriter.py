"""NODE RESPONSIBILITY
Rewrite a follow-up question into a self-contained, standalone question using
the conversation history. Skipped on turn 1 (history is empty) — passes the
original query through unchanged.

Reads:  query, history
Writes: rewritten_query
Calls:  OpenAI (rewriter_model) only if history is non-empty.
"""
from openai import OpenAI

from assistant.guidelines import REWRITER_SYSTEM_PROMPT
from assistant.settings import get_settings
from assistant.state import AssistantState


def run(state: AssistantState) -> dict:
    query = state["query"]
    history = state.get("history") or []

    if not history:
        return {
            "rewritten_query": query,
            "node_trail": ["rewriter(skipped)"],
        }

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    history_text = "\n".join(
        f'{m["role"]}: {m["content"]}' for m in history
    )
    user_prompt = (
        f"Conversation so far:\n{history_text}\n\n"
        f"New question: {query}\n\n"
        "Rewrite the new question as a standalone question."
    )

    response = client.chat.completions.create(
        model=settings.rewriter_model,
        messages=[
            {"role": "system", "content": REWRITER_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )
    rewritten = (response.choices[0].message.content or query).strip()
    return {
        "rewritten_query": rewritten,
        "node_trail": ["rewriter"],
    }
