"""NODE RESPONSIBILITY
Final node. Promotes rag_answer -> final_answer if no fallback ran, then
persists the user's query and the assistant's answer as two new rows in the
conversations table so future turns can pick them up via load_history.

Reads:  query, session_id, rag_answer, final_answer (maybe set by fallback)
Writes: final_answer
Calls:  SQLite (conversations table)
"""
from app.db.session import SessionLocal
from assistant.conversation import append_turn
from assistant.state import AssistantState


def run(state: AssistantState) -> dict:
    # If fallback did not run, promote the rag answer.
    final = state.get("final_answer") or state.get("rag_answer", "")

    with SessionLocal() as db:
        append_turn(db, state["session_id"], "user", state["query"])
        append_turn(db, state["session_id"], "assistant", final)

    return {
        "final_answer": final,
        "node_trail": ["persist_turn"],
    }
