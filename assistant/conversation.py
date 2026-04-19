"""SQLite-backed conversation store.

Defines the Conversation ORM model (registered on app.db.Base so create_all
picks it up) and two helper functions the graph nodes need:

- load_history(db, session_id, limit): fetch the last N messages in
  chronological order for a session.
- append_turn(db, session_id, role, content): add one turn and return it.
"""
from datetime import datetime
from typing import Literal

from sqlalchemy import DateTime, Integer, String, Text, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.session import Base
from assistant.state import Message


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    turn_index: Mapped[int] = mapped_column(Integer)
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


def load_history(
    db: Session, session_id: str, limit: int = 6
) -> list[Message]:
    stmt = (
        select(Conversation)
        .where(Conversation.session_id == session_id)
        .order_by(Conversation.turn_index.desc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    rows.reverse()  # restore chronological order
    return [{"role": r.role, "content": r.content} for r in rows]  # type: ignore[list-item]


def append_turn(
    db: Session,
    session_id: str,
    role: Literal["user", "assistant"],
    content: str,
) -> None:
    last_turn = db.scalar(
        select(func.max(Conversation.turn_index)).where(
            Conversation.session_id == session_id
        )
    )
    next_turn = 0 if last_turn is None else last_turn + 1
    db.add(
        Conversation(
            session_id=session_id,
            turn_index=next_turn,
            role=role,
            content=content,
        )
    )
    db.commit()
