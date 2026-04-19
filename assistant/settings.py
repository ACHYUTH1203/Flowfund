"""Assistant-specific settings.

Reuses the OpenAI key from the main app's .env. Adds RAG and LangGraph
specific knobs (model names, retrieval top-k, judge threshold).
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class AssistantSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openai_api_key: str = ""

    # Model choices. gpt-4o-mini is cheap + good enough for all three roles.
    embedding_model: str = "text-embedding-3-small"
    answer_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    rewriter_model: str = "gpt-4o-mini"

    # RAG knobs.
    retrieval_top_k: int = 4
    history_turns: int = 6  # last N turns loaded per session

    # Judge threshold: average of (relevance, groundedness, completeness)
    # below this triggers fallback for general queries.
    judge_threshold: float = 0.7

    # Filesystem paths for the FAISS index.
    index_dir: Path = Path("assistant/.faiss_index")
    corpus_dir: Path = Path("assistant/corpus")


@lru_cache
def get_settings() -> AssistantSettings:
    return AssistantSettings()
