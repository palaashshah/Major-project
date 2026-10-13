"""
Demo walk-through: five investors, from questionnaire answers to a portfolio
and its explanation. Read-only: nothing is written to the database.
"""
import os
import sys
from dataclasses import asdict
from types import SimpleNamespace

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from config.risk_constraints import PER_ASSET_CAP
from data import load_snapshot
from database import SessionLocal
from models import DataSnapshot
from optimizer.engine import InfeasiblePortfolioError, optimize_portfolio
from rationale.generator import build_rationale
from scoring.scoring import score_questionnaire

# (name, what the case shows, answers {question_id: option_index}, excluded sectors)
CASES = [
    ("1. Cautious saver",
     "Lowest answers almost everywhere.",
     {4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 0, 12: 0, 13: 1}, set()),
    ("2. Balanced professional",
     "Middle-to-high answers, long horizon.",
     {4: 2, 5: 1, 6: 2, 7: 1, 8: 2, 9: 1, 10: 2, 11: 2, 12: 2, 13: 3}, set()),
    ("3. Aggressive long-term investor",
     "Top answers everywhere.",
     {4: 2, 5: 2, 6: 3, 7: 2, 8: 3, 9: 2, 10: 3, 11: 3, 12: 3, 13: 4}, set()),
    ("4. Same as 3, but needs the money soon",
     "Shows the horizon rule capping equity.",
     {4: 0, 5: 2, 6: 3, 7: 2, 8: 3, 9: 2, 10: 3, 11: 3, 12: 3, 13: 4}, set()),
    ("5. Strong situation, weak nerves, excludes pharma",
     "Shows the lower sub-score governing, and a sector exclusion.",
     {4: 2, 5: 2, 6: 1, 7: 0, 8: 1, 9: 2, 10: 1, 11: 2, 12: 1, 13: 4}, {"pharma"}),
]


def main():
    db = SessionLocal()
    try:
        snap = db.query(DataSnapshot).order_by(DataSnapshot.created_at.desc()).first()
        if snap is None:
            sys.exit("No snapshot found. Run: python scripts/data.py")
        snapshot_id = snap.snapshot_id
        mu, cov = load_snapshot(db, snapshot_id)
    finally:
        db.close()

    weights, summary = {}, {}
    for name, shows, answers, excluded in CASES:
        print("=" * 78)
        print(name)
        print(shows)
        print("=" * 78)

        scored = score_questionnaire(answers)
        try:
            result = optimize_portfolio(mu, cov, scored.constraints, excluded_sectors=frozenset(excluded))
        except InfeasiblePortfolioError as exc:
            print(f"No portfolio possible: {exc}\n")
            continue

        assessment = SimpleNamespace(
            capacity_score=scored.capacity_score, tolerance_score=scored.tolerance_score,
            score=scored.score, limited_by=scored.limited_by, horizon=scored.horizon,
            notes=list(scored.notes))
        portfolio = SimpleNamespace(
            constraints={**asdict(scored.constraints), "per_asset_cap": PER_ASSET_CAP},
            objective_used=result.objective_used, risk_free_rate=result.risk_free_rate,
            excluded_sectors=sorted(excluded), unmatched_exclusions=[],
            snapshot_id=snapshot_id, weights=result.weights,
            expected_return=result.expected_return, volatility=result.volatility,
            sharpe=result.sharpe, binding=result.binding)
        print(build_rationale(assessment, portfolio, mu, cov).as_text())
        print()

        short = name.split(".")[0]
        weights[short] = result.weights
        summary[short] = {
            "score": scored.score,
            "equity_min": scored.constraints.min_equity,
            "equity_max": scored.constraints.max_equity,
            "return": result.expected_return,
            "volatility": result.volatility,
        }

    pd.set_option("display.width", 200)
    print("=" * 78)
    print("ALL FIVE SIDE BY SIDE (columns are the case numbers)")
    print("=" * 78)
    print((pd.DataFrame(weights) * 100).round(1).to_string())
    print()
    table = pd.DataFrame(summary)
    table.loc[["equity_min", "equity_max", "return", "volatility"]] *= 100
    print(table.round(1).to_string())
    print("\n(weights, equity limits, return and volatility are in percent)")


if __name__ == "__main__":
    main()

# to run 
#   cd backend && python scripts/demo.py > demo_output.txt