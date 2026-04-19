"""OpenAI embeddings wrapper.

Turns text into float vectors via the OpenAI embeddings API. Batches multiple
texts in a single call for efficiency when seeding the corpus.
"""
from openai import OpenAI

from assistant.settings import get_settings

_settings = get_settings()
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=_settings.openai_api_key)
    return _client


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = _get_client().embeddings.create(
        model=_settings.embedding_model,
        input=texts,
    )
    return [row.embedding for row in response.data]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
