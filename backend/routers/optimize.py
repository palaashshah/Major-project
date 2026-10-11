"""
Optimization endpoints.

WHY: the API orchestrates every step (PRD 7.2). It gathers the investor's
assessment, exclusions and a stored data snapshot, calls the pure optimizer,
then saves the run with everything needed to reproduce it, plus an audit row.
"""
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.risk_constraints import ASSETS, PER_ASSET_CAP, RISK_FREE_RATE
from database import get_db
from models import AuditLog, DataSnapshot, Investor, Portfolio, RiskAssessment
from optimizer.engine import (
    InfeasiblePortfolioError,
    evaluate_constraints,
    optimize_portfolio,
    portfolio_metrics,
)
from schemas import MetricsRequest, MetricsResponse, OptimizeRequest, PortfolioResponse
from scoring.scoring import constraints_for_score
from scripts.data import load_snapshot

router = APIRouter(tags=["Optimization"])

KNOWN_SECTORS = {a.sector for a in ASSETS if a.sector}


def load_context(db: Session, investor_id: str, snapshot_id):
    """Collect everything an optimization needs for one investor."""
    investor = db.query(Investor).filter(Investor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.investor_id == investor_id)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )
    if not assessment:
        raise HTTPException(
            status_code=409,
            detail="This investor has no risk assessment yet. Submit the questionnaire first.")

    constraints = constraints_for_score(assessment.score, assessment.horizon)

    # Exclusions are matched to ETF sector tags; anything else is reported back.
    requested = [str(s) for s in (investor.preferences_constraints or {}).get("excluded_sectors", [])]
    matched = sorted({s.lower() for s in requested} & KNOWN_SECTORS)
    unmatched = sorted(s for s in requested if s.lower() not in KNOWN_SECTORS)

    if snapshot_id is None:
        latest = db.query(DataSnapshot).order_by(DataSnapshot.created_at.desc()).first()
        if not latest:
            raise HTTPException(
                status_code=409,
                detail="No market data snapshot exists. Run scripts/data.py first.")
        snapshot_id = latest.snapshot_id
    try:
        mu, cov = load_snapshot(db, snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    return investor, assessment, constraints, matched, unmatched, snapshot_id, mu, cov


@router.post("/optimize", response_model=PortfolioResponse)
def run_optimization(body: OptimizeRequest, db: Session = Depends(get_db)):
    investor, assessment, constraints, matched, unmatched, snapshot_id, mu, cov = load_context(
        db, body.investor_id, body.snapshot_id)

    try:
        result = optimize_portfolio(mu, cov, constraints, excluded_sectors=frozenset(matched))
    except InfeasiblePortfolioError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ValueError as exc:   # snapshot and config disagree about the tickers
        raise HTTPException(status_code=409, detail=str(exc))

    now = datetime.now(timezone.utc)
    portfolio = Portfolio(
        id=str(uuid.uuid4()),
        investor_id=investor.id,
        assessment_id=assessment.id,
        snapshot_id=snapshot_id,
        created_at=now,
        created_by=body.requested_by or investor.assigned_manager_id,
        status="proposed",
        constraints={**asdict(constraints), "per_asset_cap": PER_ASSET_CAP},
        excluded_sectors=matched,
        unmatched_exclusions=unmatched,
        risk_free_rate=result.risk_free_rate,
        objective_used=result.objective_used,
        weights=result.weights,
        expected_return=result.expected_return,
        volatility=result.volatility,
        sharpe=result.sharpe,
        binding=result.binding,
    )
    db.add(portfolio)
    db.add(AuditLog(
        id=str(uuid.uuid4()),
        timestamp=now,
        user_id=portfolio.created_by,
        action="portfolio.optimized",
        entity_type="portfolio",
        entity_id=portfolio.id,
        after={"investor_id": investor.id, "snapshot_id": str(snapshot_id), "weights": result.weights},
    ))
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.post("/optimize/metrics", response_model=MetricsResponse)
def recompute_metrics(body: MetricsRequest, db: Session = Depends(get_db)):
    """Metrics and rule checks for manually edited weights. Saves nothing."""
    _, _, constraints, matched, _, _, mu, cov = load_context(db, body.investor_id, body.snapshot_id)

    unknown = sorted(set(body.weights) - set(mu.index))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown tickers: {unknown}")

    weights = pd.Series(body.weights, dtype=float).reindex(mu.index).fillna(0.0)
    expected_return, volatility, sharpe = portfolio_metrics(weights, mu, cov, RISK_FREE_RATE)
    binding, violations = evaluate_constraints(weights, volatility, constraints, frozenset(matched))
    return MetricsResponse(
        expected_return=expected_return, volatility=volatility, sharpe=sharpe,
        binding=binding, violations=violations)


@router.get("/portfolios", response_model=list[PortfolioResponse])
def list_portfolios(investor_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Portfolio)
    if investor_id:
        query = query.filter(Portfolio.investor_id == investor_id)
    return query.order_by(Portfolio.created_at.desc()).all()


@router.get("/portfolios/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio