"""
Seeds ONE demonstration portfolio that started in the past, so valuation and
drift have something to show.

It rebuilds the return and risk estimates from prices up to a past date only,
runs the optimizer on those, and records the portfolio as accepted on that
date. The optimizer therefore never sees the period it is later valued on.
Everything it creates is marked as seeded in the audit log.

Usage (from backend/):  python scripts/seed_demo_portfolio.py <investor_id> [days_ago]
"""
import os
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from config.risk_constraints import ASSETS, PER_ASSET_CAP
from data import compute_mean_and_cov, compute_monthly_returns, save_snapshot
from database import SessionLocal
from models import (
    AuditLog, DataSnapshot, Investor, MarketData, Portfolio, PortfolioDecision, RiskAssessment,
)
from optimizer.engine import optimize_portfolio
from scoring.scoring import constraints_for_score

KNOWN_SECTORS = {a.sector for a in ASSETS if a.sector}
SEED_NOTE = "Demonstration data: backdated portfolio created by seed_demo_portfolio.py"


def main():
    if len(sys.argv) < 2:
        sys.exit("Usage: python scripts/seed_demo_portfolio.py <investor_id> [days_ago]")
    investor_id = sys.argv[1]
    days_ago = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    start = now - timedelta(days=days_ago)

    db = SessionLocal()
    try:
        investor = db.query(Investor).filter(Investor.id == investor_id).first()
        if not investor:
            sys.exit("Investor not found.")
        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.investor_id == investor_id)
            .order_by(RiskAssessment.created_at.desc())
            .first()
        )
        if not assessment:
            sys.exit("This investor has no risk assessment. Submit the questionnaire first.")
        if not investor.total_aum or float(investor.total_aum) <= 0:
            sys.exit("This investor has no total_aum to invest.")

        # 1. Stored prices, cut off at the past date.
        tickers = [a.ticker for a in ASSETS]
        rows = (
            db.query(MarketData.asset_symbol, MarketData.date, MarketData.close_price)
            .filter(MarketData.asset_symbol.in_(tickers))
            .all()
        )
        if not rows:
            sys.exit("No stored prices. Run: python scripts/data.py")
        frame = pd.DataFrame(rows, columns=["ticker", "date", "price"])
        frame["price"] = frame["price"].astype(float)
        frame["date"] = pd.to_datetime(frame["date"])
        prices = frame.pivot(index="date", columns="ticker", values="price").sort_index()
        past = prices.loc[:pd.Timestamp(start.date())]
        if len(past) < 500:
            sys.exit("Not enough price history before that date.")

        # 2. Estimates from the past only, saved as a snapshot dated in the past.
        mu, cov = compute_mean_and_cov(compute_monthly_returns(past))
        snapshot_id = save_snapshot(db, mu, cov)
        db.query(DataSnapshot).filter(DataSnapshot.snapshot_id == snapshot_id).update({"created_at": start})

        # 3. Optimize exactly as the API would.
        constraints = constraints_for_score(assessment.score, assessment.horizon)
        requested = [str(s) for s in (investor.preferences_constraints or {}).get("excluded_sectors", [])]
        matched = sorted({s.lower() for s in requested} & KNOWN_SECTORS)
        unmatched = sorted(s for s in requested if s.lower() not in KNOWN_SECTORS)
        result = optimize_portfolio(mu, cov, constraints, excluded_sectors=frozenset(matched))

        # 4. One active portfolio per investor: retire any earlier accepted one.
        for old in db.query(Portfolio).filter(Portfolio.investor_id == investor_id,
                                              Portfolio.status == "accepted").all():
            old.status = "superseded"

        # 5. Record the portfolio and its decisions, dated in the past.
        manager = investor.assigned_manager_id
        portfolio = Portfolio(
            id=str(uuid.uuid4()), investor_id=investor_id, assessment_id=assessment.id,
            snapshot_id=snapshot_id, created_at=start, created_by=manager, status="accepted",
            constraints={**asdict(constraints), "per_asset_cap": PER_ASSET_CAP},
            excluded_sectors=matched, unmatched_exclusions=unmatched,
            risk_free_rate=result.risk_free_rate, objective_used=result.objective_used,
            weights=result.weights, expected_return=result.expected_return,
            volatility=result.volatility, sharpe=result.sharpe, binding=result.binding)
        db.add(portfolio)
        db.flush()
        db.add(PortfolioDecision(
            id=str(uuid.uuid4()), portfolio_id=portfolio.id, timestamp=start, actor="manager",
            decision="approved", reason=SEED_NOTE, recorded_by=manager))
        db.add(PortfolioDecision(
            id=str(uuid.uuid4()), portfolio_id=portfolio.id, timestamp=start, actor="client",
            decision="accepted", reason=SEED_NOTE, recorded_by=manager,
            amount=float(investor.total_aum)))
        db.add(AuditLog(
            id=str(uuid.uuid4()), timestamp=now, user_id=manager, action="portfolio.seeded",
            entity_type="portfolio", entity_id=portfolio.id, reason=SEED_NOTE,
            after={"status": "accepted", "dated": str(start.date()), "snapshot_id": str(snapshot_id)}))
        db.commit()

        print(f"Seeded portfolio {portfolio.id}, dated {start.date()}")
        print(pd.Series(result.weights).loc[lambda s: s > 0].map("{:.1%}".format).to_string())
        print(f"\nNow open: GET /portfolios/{portfolio.id}/valuation")
    finally:
        db.close()


if __name__ == "__main__":
    main()