"""LangGraph definition: wires every node module into a StateGraph with a
conditional edge after the judge that routes weak general-query answers to
the fallback node.
"""
import logging
import time
from functools import wraps

from langgraph.graph import END, START, StateGraph

from assistant import (
    fallback,
    fetch_context,
    judge,
    load_history,
    persist_turn,
    rag_answer,
    retriever,
    rewriter,
)
from assistant.state import AssistantState

logger = logging.getLogger("assistant.graph")


def _logged(name: str, run_fn):
    """Wrap a node's run() so every invocation is logged with session_id and
    elapsed time. Exceptions are logged with traceback before re-raising so
    the real error still surfaces to the graph caller.
    """

    @wraps(run_fn)
    def wrapper(state: AssistantState) -> dict:
        session = state.get("session_id", "?")
        started = time.time()
        logger.info("[%s] -> %s", session, name)
        try:
            result = run_fn(state)
        except Exception:
            logger.exception(
                "[%s] %s failed after %.0fms",
                session,
                name,
                (time.time() - started) * 1000,
            )
            raise
        logger.info(
            "[%s] <- %s  (%.0fms)",
            session,
            name,
            (time.time() - started) * 1000,
        )
        return result

    return wrapper


def _route_after_judge(state: AssistantState) -> str:
    verdict = state.get("judge_verdict", {}).get("verdict", "keep")
    is_personal = bool(state.get("is_personal", False))
    route = "fallback" if verdict == "fallback" and not is_personal else "persist_turn"
    logger.info(
        "[%s] judge verdict=%s is_personal=%s -> %s",
        state.get("session_id", "?"),
        verdict,
        is_personal,
        route,
    )
    return route


def build_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("load_history", _logged("load_history", load_history.run))
    graph.add_node("rewriter", _logged("rewriter", rewriter.run))
    graph.add_node("fetch_context", _logged("fetch_context", fetch_context.run))
    graph.add_node("retriever", _logged("retriever", retriever.run))
    graph.add_node("rag_answer", _logged("rag_answer", rag_answer.run))
    graph.add_node("judge", _logged("judge", judge.run))
    graph.add_node("fallback", _logged("fallback", fallback.run))
    graph.add_node("persist_turn", _logged("persist_turn", persist_turn.run))

    graph.add_edge(START, "load_history")
    graph.add_edge("load_history", "rewriter")
    graph.add_edge("rewriter", "fetch_context")
    graph.add_edge("fetch_context", "retriever")
    graph.add_edge("retriever", "rag_answer")
    graph.add_edge("rag_answer", "judge")
    graph.add_conditional_edges(
        "judge",
        _route_after_judge,
        {
            "fallback": "fallback",
            "persist_turn": "persist_turn",
        },
    )
    graph.add_edge("fallback", "persist_turn")
    graph.add_edge("persist_turn", END)

    return graph.compile()
