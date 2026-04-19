"""NODE RESPONSIBILITY
Invoked when the judge flags the RAG answer as weak AND the query is not
personal (we never fall back for personal queries — inventing user data would
be worse than admitting uncertainty). Produces a plain-LLM answer to the
rewritten query with no chunks and no DB context.

Reads:  rewritten_query
Writes: final_answer, used_fallback=True
Calls:  OpenAI (answer_model)
"""
from openai import OpenAI

from assistant.guidelines import FALLBACK_SYSTEM_PROMPT
from assistant.settings import get_settings
from assistant.state import AssistantState


def run(state: AssistantState) -> dict:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)
    query = state.get("rewritten_query") or state["query"]

    response = client.chat.completions.create(
        model=settings.answer_model,
        messages=[
            {"role": "system", "content": FALLBACK_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0.2,
    )
    answer = (response.choices[0].message.content or "").strip()
    return {
        "final_answer": answer,
        "used_fallback": True,
        "node_trail": ["fallback"],
    }
