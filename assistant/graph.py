"""LangGraph definition: wires every node module into a StateGraph with a
conditional edge after the judge that routes weak general-query answers to
the fallback node.
"""
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


def _route_after_judge(state: AssistantState) -> str:
    verdict = state.get("judge_verdict", {}).get("verdict", "keep")
    is_personal = bool(state.get("is_personal", False))
    if verdict == "fallback" and not is_personal:
        return "fallback"
    return "persist_turn"


def build_graph():
    graph = StateGraph(AssistantState)

    graph.add_node("load_history", load_history.run)
    graph.add_node("rewriter", rewriter.run)
    graph.add_node("fetch_context", fetch_context.run)
    graph.add_node("retriever", retriever.run)
    graph.add_node("rag_answer", rag_answer.run)
    graph.add_node("judge", judge.run)
    graph.add_node("fallback", fallback.run)
    graph.add_node("persist_turn", persist_turn.run)

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
