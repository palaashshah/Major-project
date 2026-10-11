"""
Approval workflow endpoints (PRD stages 4 and 6).

WHY: human oversight is a core goal, so no portfolio becomes "accepted"
without a manager approving it and the client's answer being logged. Every
decision is an append-only row plus an audit row.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import AuditLog, Investor, Portfolio, PortfolioDecision
from schemas import (
    ClientDecisionRequest,
    ManagerDecisionRequest,
    PortfolioDecisionResponse,
    PortfolioResponse,
)

router = APIRouter(tags=["Decisions"])


def get_portfolio_or_404(db: Session, portfolio_id: str) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


def change_status(db: Session, portfolio: Portfolio, new_status: str,
                  user_id: str, reason: Optional[str]) -> None:
    """Set a new status and write the audit row for it. The caller commits."""
    before = portfolio.status
    portfolio.status = new_status
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        user_id=user_id,
        action=f"portfolio.{new_status}",
        entity_type="portfolio",
        entity_id=portfolio.id,
        reason=reason,
        before={"status": before},
        after={"status": new_status},
    ))


def add_decision(db: Session, portfolio: Portfolio, actor: str, decision: str,
                 reason: Optional[str], recorded_by: str, amount: Optional[float] = None) -> None:
    db.add(PortfolioDecision(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio.id,
        timestamp=datetime.now(timezone.utc),
        actor=actor,
        decision=decision,
        reason=reason,
        recorded_by=recorded_by,
        amount=amount,
    ))


@router.post("/portfolios/{portfolio_id}/manager-decision", response_model=PortfolioResponse)
def manager_decision(portfolio_id: str, body: ManagerDecisionRequest, db: Session = Depends(get_db)):
    portfolio = get_portfolio_or_404(db, portfolio_id)
    if portfolio.status != "proposed":
        raise HTTPException(
            status_code=409,
            detail=f"Only a proposed portfolio can be approved or rejected; this one is {portfolio.status}.")
    if body.decision == "rejected" and not (body.reason or "").strip():
        raise HTTPException(status_code=422, detail="A reason is required to reject a portfolio.")

    add_decision(db, portfolio, "manager", body.decision, body.reason, body.decided_by)
    change_status(db, portfolio, body.decision, body.decided_by, body.reason)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.post("/portfolios/{portfolio_id}/client-decision", response_model=PortfolioResponse)
def client_decision(portfolio_id: str, body: ClientDecisionRequest, db: Session = Depends(get_db)):
    portfolio = get_portfolio_or_404(db, portfolio_id)
    if portfolio.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"The client can only decide on an approved portfolio; this one is {portfolio.status}.")

    amount = None
    if body.decision == "accepted":
        investor = db.query(Investor).filter(Investor.id == portfolio.investor_id).first()
        amount = body.amount
        if amount is None and investor.total_aum is not None:
            amount = float(investor.total_aum)
        if amount is None or amount <= 0:
            raise HTTPException(
                status_code=422,
                detail="An invested amount is required: send 'amount' or set the investor's total_aum.")

        # An investor has one active portfolio: retire any earlier accepted one.
        earlier = (
            db.query(Portfolio)
            .filter(Portfolio.investor_id == portfolio.investor_id,
                    Portfolio.status == "accepted",
                    Portfolio.id != portfolio.id)
            .all()
        )
        for old in earlier:
            change_status(db, old, "superseded", body.recorded_by, f"Replaced by portfolio {portfolio.id}")

    add_decision(db, portfolio, "client", body.decision, body.notes, body.recorded_by, amount)
    change_status(db, portfolio, body.decision, body.recorded_by, body.notes)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/portfolios/{portfolio_id}/decisions", response_model=list[PortfolioDecisionResponse])
def list_decisions(portfolio_id: str, db: Session = Depends(get_db)):
    get_portfolio_or_404(db, portfolio_id)
    return (
        db.query(PortfolioDecision)
        .filter(PortfolioDecision.portfolio_id == portfolio_id)
        .order_by(PortfolioDecision.timestamp)
        .all()
    )