"""NODE RESPONSIBILITY
Embed the (rewritten) query and search the FAISS index for top-k chunks from
our corpus. Always runs — even for personal queries — so the answer node can
mix in product/regulation context when relevant.

Reads:  rewritten_query (falls back to query)
Writes: retrieved_chunks (list[Chunk])
Calls:  OpenAI (embeddings), FAISS (local file)
"""
from assistant.embedder import embed_query
from assistant.settings import get_settings
from assistant.state import AssistantState
from assistant.vector_store import VectorStore

_store: VectorStore | None = None


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        settings = get_settings()
        _store = VectorStore.load(settings.index_dir)
    return _store


def run(state: AssistantState) -> dict:
    settings = get_settings()
    query = state.get("rewritten_query") or state["query"]
    q_vec = embed_query(query)
    hits = _get_store().search(q_vec, k=settings.retrieval_top_k)
    chunks = [
        {"text": h.text, "source": h.source, "score": h.score} for h in hits
    ]
    return {
        "retrieved_chunks": chunks,
        "node_trail": ["retriever"],
    }
