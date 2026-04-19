"""One-shot script: read the corpus, embed each file as one chunk,
and write a FAISS index to disk.

Usage (from project root):
    poetry run python scripts/seed_rag.py
"""
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `import assistant.*` works
# regardless of where the script is invoked from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from assistant.embedder import embed_texts
from assistant.settings import get_settings
from assistant.vector_store import VectorStore


def main() -> None:
    settings = get_settings()
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is not set in .env")

    corpus_dir = settings.corpus_dir
    if not corpus_dir.exists():
        raise SystemExit(f"Corpus directory not found: {corpus_dir}")

    md_files = sorted(corpus_dir.rglob("*.md"))
    if not md_files:
        raise SystemExit(f"No .md files found under {corpus_dir}")

    texts: list[str] = []
    meta: list[dict] = []
    for path in md_files:
        text = path.read_text(encoding="utf-8").strip()
        source = str(path.relative_to(corpus_dir)).replace("\\", "/")
        texts.append(text)
        meta.append({"source": source, "text": text})

    print(f"Embedding {len(texts)} chunks with {settings.embedding_model} ...")
    embeddings = embed_texts(texts)
    dim = len(embeddings[0])
    print(f"Got {len(embeddings)} vectors of dim {dim}")

    store = VectorStore(dim=dim)
    store.add(embeddings, meta)
    store.save(settings.index_dir)
    print(f"Saved FAISS index to {settings.index_dir}")

    # Quick sanity probe.
    from assistant.embedder import embed_query
    query = "why is my risk high?"
    q_vec = embed_query(query)
    hits = store.search(q_vec, k=3)
    print(f"\nSanity check — query: {query!r}")
    for h in hits:
        print(f"  score={h.score:.3f}  source={h.source}")


if __name__ == "__main__":
    main()
