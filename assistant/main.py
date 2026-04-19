"""Entry point for the assistant graph.

Compiles the StateGraph once (lazily) and exposes run_assistant(...) for the
/ask API layer to call. Keeping the compiled graph in a module-level cache
avoids rebuilding it per request.
"""
from assistant.graph import build_graph
from assistant.state import AssistantState

_compiled = None


def get_graph():
    global _compiled
    if _compiled is None:
        _compiled = build_graph()
    return _compiled


def run_assistant(
    query: str,
    session_id: str,
    loan_id: int | None = None,
) -> AssistantState:
    graph = get_graph()
    initial: AssistantState = {
        "query": query,
        "session_id": session_id,
        "loan_id": loan_id,
        "node_trail": [],
    }
    return graph.invoke(initial)
