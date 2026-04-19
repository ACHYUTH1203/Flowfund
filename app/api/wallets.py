from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.transaction import TransactionOut
from app.schemas.wallet import (
    AddFundsRequest,
    AddFundsResponse,
    DebitRequest,
    DebitResponse,
    WalletCreate,
    WalletOut,
)
from app.services import wallet as wallet_service

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("", response_model=WalletOut, status_code=201)
def create_wallet(
    payload: WalletCreate,
    db: Session = Depends(get_db),
) -> WalletOut:
    return wallet_service.create_wallet(db, user_id=payload.user_id)


@router.get("/{wallet_id}", response_model=WalletOut)
def get_wallet(wallet_id: int, db: Session = Depends(get_db)) -> WalletOut:
    return wallet_service.get_wallet(db, wallet_id)


@router.post("/{wallet_id}/add-funds", response_model=AddFundsResponse, status_code=201)
def add_funds(
    wallet_id: int,
    payload: AddFundsRequest,
    db: Session = Depends(get_db),
) -> dict:
    txn, wallet = wallet_service.add_funds(
        db,
        wallet_id=wallet_id,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
        note=payload.note,
    )
    return {"transaction": txn, "wallet": wallet}


@router.post("/{wallet_id}/debit", response_model=DebitResponse, status_code=201)
def debit(
    wallet_id: int,
    payload: DebitRequest,
    db: Session = Depends(get_db),
) -> dict:
    txn, wallet = wallet_service.debit(
        db,
        wallet_id=wallet_id,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
        loan_id=payload.loan_id,
        note=payload.note,
    )
    return {"transaction": txn, "wallet": wallet}


@router.get("/{wallet_id}/transactions", response_model=list[TransactionOut])
def list_transactions(
    wallet_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return wallet_service.list_transactions(
        db, wallet_id=wallet_id, limit=limit, offset=offset
    )
