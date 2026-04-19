from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TxnStatus, TxnType
from app.models.wallet import Wallet


def create_wallet(db: Session, user_id: str) -> Wallet:
    wallet = Wallet(user_id=user_id, balance=Decimal("0.00"))
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def get_wallet(db: Session, wallet_id: int) -> Wallet:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


def add_funds(
    db: Session,
    wallet_id: int,
    amount: Decimal,
    idempotency_key: str | None = None,
    note: str | None = None,
) -> tuple[Transaction, Wallet]:
    # Idempotent replay: same key → return the stored result.
    if idempotency_key:
        existing = db.scalar(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        if existing is not None:
            wallet = db.get(Wallet, existing.wallet_id)
            return existing, wallet

    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    txn = Transaction(
        wallet_id=wallet.id,
        amount=amount,
        type=TxnType.credit,
        status=TxnStatus.success,
        idempotency_key=idempotency_key,
        note=note,
    )
    wallet.balance = wallet.balance + amount
    db.add(txn)
    db.commit()
    db.refresh(txn)
    db.refresh(wallet)
    return txn, wallet


def debit(
    db: Session,
    wallet_id: int,
    amount: Decimal,
    idempotency_key: str | None = None,
    loan_id: int | None = None,
    note: str | None = None,
) -> tuple[Transaction, Wallet]:
    if idempotency_key:
        existing = db.scalar(
            select(Transaction).where(Transaction.idempotency_key == idempotency_key)
        )
        if existing is not None:
            wallet = db.get(Wallet, existing.wallet_id)
            return existing, wallet

    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    if wallet.balance >= amount:
        status = TxnStatus.success
        wallet.balance = wallet.balance - amount
    else:
        status = TxnStatus.skipped

    txn = Transaction(
        wallet_id=wallet.id,
        loan_id=loan_id,
        amount=amount,
        type=TxnType.debit,
        status=status,
        idempotency_key=idempotency_key,
        note=note,
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    db.refresh(wallet)
    return txn, wallet


def list_transactions(
    db: Session,
    wallet_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[Transaction]:
    wallet = db.get(Wallet, wallet_id)
    if wallet is None:
        raise HTTPException(status_code=404, detail="Wallet not found")

    stmt = (
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(Transaction.created_at.desc(), Transaction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())
