"""FAISS-based vector store for the corpus.

Stores two artefacts side by side on disk:
- index.faiss: the FAISS index (flat L2 on normalised vectors = cosine similarity)
- meta.json: one record per vector with {source, text}, aligned by position.

Design is intentionally minimal: load/save are whole-file; search returns
(score, source, text) tuples. Fine for ~40 chunks.
"""
import json
from dataclasses import dataclass
from pathlib import Path

import faiss
import numpy as np


@dataclass(frozen=True)
class SearchHit:
    source: str
    text: str
    score: float


class VectorStore:
    def __init__(self, dim: int):
        self.dim = dim
        # IndexFlatIP on L2-normalised vectors == cosine similarity.
        self.index = faiss.IndexFlatIP(dim)
        self.meta: list[dict] = []  # each: {"source": ..., "text": ...}

    def add(self, embeddings: list[list[float]], meta: list[dict]) -> None:
        if len(embeddings) != len(meta):
            raise ValueError("embeddings and meta must be same length")
        vectors = np.asarray(embeddings, dtype="float32")
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        self.meta.extend(meta)

    def search(self, query_embedding: list[float], k: int) -> list[SearchHit]:
        if self.index.ntotal == 0:
            return []
        q = np.asarray([query_embedding], dtype="float32")
        faiss.normalize_L2(q)
        k = min(k, self.index.ntotal)
        scores, indices = self.index.search(q, k)
        hits: list[SearchHit] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            m = self.meta[idx]
            hits.append(SearchHit(source=m["source"], text=m["text"], score=float(score)))
        return hits

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(index_dir / "index.faiss"))
        (index_dir / "meta.json").write_text(
            json.dumps(self.meta, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, index_dir: Path) -> "VectorStore":
        index_path = index_dir / "index.faiss"
        meta_path = index_dir / "meta.json"
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"FAISS index not found at {index_dir}. "
                "Run scripts/seed_rag.py first."
            )
        index = faiss.read_index(str(index_path))
        store = cls.__new__(cls)
        store.dim = index.d
        store.index = index
        store.meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return store
