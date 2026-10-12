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

from config.risk_constraints import ASSETS, PER_ASSET_CAP, RISK_FREE_RATE, BucketConstraints
from database import get_db
from models import AuditLog, DataSnapshot, Investor, Portfolio, RiskAssessment
from optimizer.engine import (
    InfeasiblePortfolioError,
    evaluate_constraints,
    optimize_portfolio,
    portfolio_metrics,
)
from schemas import (
    AdjustRequest, MetricsRequest, MetricsResponse, OptimizeRequest,
    PortfolioResponse, RationaleResponse,
)
from scoring.scoring import constraints_for_score
from scripts.data import load_snapshot
from rationale.generator import build_rationale

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

@router.get("/portfolios/{portfolio_id}/rationale", response_model=RationaleResponse)
def get_rationale(portfolio_id: str, db: Session = Depends(get_db)):
    """The explanation for one saved portfolio, rebuilt from stored values."""
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    assessment = db.query(RiskAssessment).filter(RiskAssessment.id == portfolio.assessment_id).first()
    try:
        mu, cov = load_snapshot(db, portfolio.snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    rationale = build_rationale(assessment, portfolio, mu, cov)
    return {"portfolio_id": portfolio.id, **asdict(rationale), "text": rationale.as_text()}

def stored_constraints(portfolio: Portfolio) -> BucketConstraints:
    """Rebuild the limits a portfolio was created under, from what was saved with it."""
    c = portfolio.constraints
    return BucketConstraints(
        name=c["name"], score_min=c["score_min"], score_max=c["score_max"],
        max_equity=c["max_equity"], max_volatility=c["max_volatility"],
        min_defensive=c["min_defensive"], objective=c["objective"],
        min_equity=c["min_equity"])


@router.post("/portfolios/{portfolio_id}/adjust", response_model=PortfolioResponse)
def adjust_weights(portfolio_id: str, body: AdjustRequest, db: Session = Depends(get_db)):
    """Save manager-edited weights as a new proposed portfolio (PRD 5.6).
    A portfolio that breaks any rule is refused, never saved silently."""
    source = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    if source.status != "proposed":
        raise HTTPException(
            status_code=409,
            detail=f"Only a proposed portfolio can be adjusted; this one is {source.status}.")
    if not body.reason.strip():
        raise HTTPException(status_code=422, detail="A reason is required to adjust weights.")

    try:
        mu, cov = load_snapshot(db, source.snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    unknown = sorted(set(body.weights) - set(mu.index))
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown tickers: {unknown}")

    weights = pd.Series(body.weights, dtype=float).reindex(mu.index).fillna(0.0).round(6)
    constraints = stored_constraints(source)
    expected_return, volatility, sharpe = portfolio_metrics(weights, mu, cov, source.risk_free_rate)
    binding, violations = evaluate_constraints(
        weights, volatility, constraints, frozenset(source.excluded_sectors))
    if violations:
        raise HTTPException(status_code=422, detail={
            "message": "The adjusted weights break one or more rules, so they were not saved.",
            "violations": violations})

    now = datetime.now(timezone.utc)
    adjusted = Portfolio(
        id=str(uuid.uuid4()),
        investor_id=source.investor_id,
        assessment_id=source.assessment_id,
        snapshot_id=source.snapshot_id,
        created_at=now,
        created_by=body.adjusted_by,
        status="proposed",
        constraints=source.constraints,
        excluded_sectors=source.excluded_sectors,
        unmatched_exclusions=source.unmatched_exclusions,
        risk_free_rate=source.risk_free_rate,
        objective_used="manual_adjustment",
        weights={ticker: float(w) for ticker, w in weights.items()},
        expected_return=expected_return,
        volatility=volatility,
        sharpe=sharpe,
        binding=binding,
    )
    db.add(adjusted)
    source.status = "superseded"

    db.add(AuditLog(
        id=str(uuid.uuid4()), timestamp=now, user_id=body.adjusted_by,
        action="portfolio.adjusted", entity_type="portfolio", entity_id=adjusted.id,
        reason=body.reason,
        before={"portfolio_id": source.id, "weights": source.weights},
        after={"portfolio_id": adjusted.id, "weights": adjusted.weights}))
    db.add(AuditLog(
        id=str(uuid.uuid4()), timestamp=now, user_id=body.adjusted_by,
        action="portfolio.superseded", entity_type="portfolio", entity_id=source.id,
        reason=f"Adjusted into portfolio {adjusted.id}",
        before={"status": "proposed"}, after={"status": "superseded"}))
    db.commit()
    db.refresh(adjusted)
    return adjusted