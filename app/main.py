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
from app.db.session import Base, engine, get_db
import app.models  # noqa: F401  -- registers models on Base.metadata
import assistant.conversation  # noqa: F401  -- registers Conversation table
from assistant.api import router as ask_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="ClickPe Lite", version="0.1.0", lifespan=lifespan)

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
# The directory only exists in production (after `npm run build`) — the guard
# keeps local dev working without the build output.
_FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="frontend",
    )
