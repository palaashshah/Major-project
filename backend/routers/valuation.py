"""
Valuation and drift endpoints.

WHY: gives the manager the current paper value of an accepted portfolio and
raises the "rebalancing suggested" flag when a holding drifts past the
threshold. Reads stored prices only; never downloads.
"""
from dataclasses import asdict
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import MarketData, Portfolio, PortfolioDecision
from schemas import ValuationResponse
from valuation.valuation import value_portfolio

router = APIRouter(tags=["Valuation"])


def load_prices(db: Session, tickers: list[str]) -> pd.DataFrame:
    rows = (
        db.query(MarketData.asset_symbol, MarketData.date, MarketData.close_price)
        .filter(MarketData.asset_symbol.in_(tickers))
        .all()
    )
    if not rows:
        raise HTTPException(status_code=409, detail="No stored prices. Run scripts/data.py first.")
    frame = pd.DataFrame(rows, columns=["ticker", "date", "price"])
    frame["price"] = frame["price"].astype(float)
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.pivot(index="date", columns="ticker", values="price").sort_index()


def build_valuation(db: Session, portfolio: Portfolio, invested_on: Optional[date]) -> dict:
    accepted = (
        db.query(PortfolioDecision)
        .filter(PortfolioDecision.portfolio_id == portfolio.id,
                PortfolioDecision.actor == "client",
                PortfolioDecision.decision == "accepted")
        .order_by(PortfolioDecision.timestamp.desc())
        .first()
    )
    if accepted is None:
        raise HTTPException(
            status_code=409,
            detail="This portfolio has not been accepted by the client, so there is nothing to value.")

    held = [t for t, w in portfolio.weights.items() if w > 0]
    prices = load_prices(db, held)
    try:
        valuation = value_portfolio(
            portfolio.weights, float(accepted.amount), prices,
            invested_on or accepted.timestamp.date(),
            cash_rate=portfolio.risk_free_rate)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    return {
        "portfolio_id": portfolio.id,
        "investor_id": portfolio.investor_id,
        "hypothetical": invested_on is not None,
        **asdict(valuation),
    }


@router.get("/portfolios/{portfolio_id}/valuation", response_model=ValuationResponse)
def get_valuation(portfolio_id: str, invested_on: Optional[date] = None, db: Session = Depends(get_db)):
    """Current paper value and drift. Pass invested_on (YYYY-MM-DD) to see a
    hypothetical: what it would be worth had it been invested on that date."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return build_valuation(db, portfolio, invested_on)


@router.get("/drift-alerts", response_model=list[ValuationResponse])
def drift_alerts(db: Session = Depends(get_db)):
    """Every accepted portfolio where a holding has drifted past the threshold."""
    alerts = []
    for portfolio in db.query(Portfolio).filter(Portfolio.status == "accepted").all():
        try:
            valuation = build_valuation(db, portfolio, None)
        except HTTPException:
            continue        # no prices or no acceptance record; nothing to report
        if valuation["rebalancing_suggested"]:
            alerts.append(valuation)
    return alerts