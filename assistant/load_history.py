"""NODE RESPONSIBILITY
Load the last N conversation turns for this session_id from SQLite.

Reads:  session_id
Writes: history (list[Message])
Calls:  SQLite (conversations table)
"""
from app.db.session import SessionLocal
from assistant.conversation import load_history
from assistant.settings import get_settings
from assistant.state import AssistantState


def run(state: AssistantState) -> dict:
    settings = get_settings()
    with SessionLocal() as db:
        history = load_history(db, state["session_id"], limit=settings.history_turns)
    return {
        "history": history,
        "node_trail": ["load_history"],
    }
