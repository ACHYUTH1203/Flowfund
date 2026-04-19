"""NODE RESPONSIBILITY
Grade the RAG answer against the query and retrieved chunks on three axes.
Output a structured verdict used by the graph's conditional edge to decide
whether to keep the answer or fall back.

Reads:  rewritten_query, rag_answer, retrieved_chunks
Writes: judge_verdict
Calls:  OpenAI (judge_model) in JSON mode.
"""
import json

from openai import OpenAI

from assistant.guidelines import JUDGE_SYSTEM_PROMPT
from assistant.settings import get_settings
from assistant.state import AssistantState


def run(state: AssistantState) -> dict:
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    query = state.get("rewritten_query") or state["query"]
    answer = state.get("rag_answer", "")
    chunks = state.get("retrieved_chunks") or []
    chunks_text = "\n\n".join(c["text"] for c in chunks) or "(no chunks retrieved)"

    user_prompt = (
        f"Question:\n{query}\n\n"
        f"Retrieved knowledge:\n{chunks_text}\n\n"
        f"Answer:\n{answer}\n\n"
        "Grade and output JSON."
    )

    response = client.chat.completions.create(
        model=settings.judge_model,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    verdict = {
        "relevance": float(data.get("relevance", 0.5)),
        "groundedness": float(data.get("groundedness", 0.5)),
        "completeness": float(data.get("completeness", 0.5)),
        "verdict": "fallback" if data.get("verdict") == "fallback" else "keep",
        "reasoning": str(data.get("reasoning", "")),
    }
    avg = (
        verdict["relevance"] + verdict["groundedness"] + verdict["completeness"]
    ) / 3
    if avg < settings.judge_threshold:
        verdict["verdict"] = "fallback"

    return {
        "judge_verdict": verdict,
        "node_trail": ["judge"],
    }
