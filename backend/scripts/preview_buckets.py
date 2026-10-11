"""
Prints the per-asset sanity table and the portfolio each risk bucket gets,
using the most recent data snapshot. Read-only: writes nothing to the DB.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd

from config.risk_constraints import BUCKETS
from data import load_snapshot  # scripts/data.py, same folder as this file
from database import SessionLocal
from models import DataSnapshot
from optimizer.engine import InfeasiblePortfolioError, optimize_portfolio


def main():
    db = SessionLocal()
    try:
        snap = db.query(DataSnapshot).order_by(DataSnapshot.created_at.desc()).first()
        if snap is None:
            sys.exit("No snapshot found. Run: python scripts/data.py")
        snapshot_id, created_at = snap.snapshot_id, snap.created_at
        mu, cov = load_snapshot(db, snapshot_id)
    finally:
        db.close()

    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda x: f"{x:7.2%}")

    print(f"Snapshot {snapshot_id} (created {created_at})\n")
    print("--- Per-asset sanity table (annualised) ---")
    print(pd.DataFrame({"mean_return": mu, "volatility": np.sqrt(np.diag(cov))}))

    weights, summary = {}, {}
    for bucket in BUCKETS:
        try:
            r = optimize_portfolio(mu, cov, bucket)
        except InfeasiblePortfolioError as exc:
            print(f"\n{bucket.name}: INFEASIBLE - {exc}")
            continue
        weights[bucket.name] = r.weights
        summary[bucket.name] = {"return": r.expected_return, "volatility": r.volatility}
        print(f"\n{bucket.name}: objective={r.objective_used}, sharpe={r.sharpe:.2f}")
        for line in r.binding:
            print(f"  binding: {line}")

    print("\n--- Weights by bucket ---")
    print(pd.DataFrame(weights))
    print("\n--- Return and volatility by bucket ---")
    print(pd.DataFrame(summary))


if __name__ == "__main__":
    main()