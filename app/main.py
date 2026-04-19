import logging
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.loans import router as loans_router
from app.api.users import router as users_router
from app.api.wallets import router as wallets_router
from app.core.config import get_settings
from app.db.session import Base, engine, get_db
import app.models  # noqa: F401  -- registers models on Base.metadata
import assistant.conversation  # noqa: F401  -- registers Conversation table
from assistant.api import router as ask_router
from assistant.settings import get_settings as get_assistant_settings

# --- Logging setup ---------------------------------------------------------
# Stream to stdout at INFO so Render / Docker / uvicorn all capture the
# same output. `force=True` ensures our config wins if a library already
# called `basicConfig` during import.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
    force=True,
)
logger = logging.getLogger("app")


def _mask_db_url(url: str) -> str:
    """Strip passwords from DB URLs for safe logging."""
    return re.sub(r"://([^:/@]+):([^@]+)@", r"://\1:***@", url)


def _mask_secret(secret: str) -> str:
    """Show the last 4 chars of a secret, hide the rest."""
    if not secret:
        return "NOT SET"
    tail = secret[-4:] if len(secret) >= 4 else "?"
    return f"set (ending ...{tail})"


_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup diagnostics - everything that could bite you in production.
    settings = get_settings()
    assistant_settings = get_assistant_settings()

    logger.info("Starting FlowFund")
    logger.info("  DATABASE_URL     : %s", _mask_db_url(settings.database_url))
    logger.info("  OPENAI_API_KEY   : %s", _mask_secret(settings.openai_api_key))
    logger.info(
        "  FAISS index      : %s",
        "present"
        if assistant_settings.index_dir.exists()
        else f"MISSING at {assistant_settings.index_dir}",
    )
    logger.info(
        "  Frontend dist    : %s",
        "present (will serve at /)" if _FRONTEND_DIST.exists() else "missing (API-only mode)",
    )

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured.")

    yield

    logger.info("Shutting down.")


app = FastAPI(title="FlowFund", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(wallets_router)
app.include_router(loans_router)
app.include_router(users_router)
app.include_router(ask_router)


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    value = db.execute(text("SELECT 1")).scalar_one()
    return {"app": "ok", "db": "ok" if value == 1 else "unexpected"}


# Serve the built React frontend at /. Must come AFTER every API router
# above so API paths are matched first; anything else falls back to the SPA.
# The directory only exists in production (after `npm run build`) - the guard
# keeps local dev working without the build output.
if _FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="frontend",
    )
