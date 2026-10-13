from types import SimpleNamespace

import numpy as np
import pandas as pd

from config.risk_constraints import ASSETS
from rationale.generator import build_rationale

TICKERS = [a.ticker for a in ASSETS]


def market():
    """Simple made-up inputs: every ETF returns 10% with independent 10% volatility."""
    mu = pd.Series(0.10, index=TICKERS)
    cov = pd.DataFrame(np.eye(len(TICKERS)) * 0.01, index=TICKERS, columns=TICKERS)
    return mu, cov


def stored_rows(horizon="long", score=28, min_equity=0.304, max_equity=0.344):
    assessment = SimpleNamespace(
        capacity_score=100, tolerance_score=score, score=score, limited_by="tolerance",
        horizon=horizon, notes=["Capacity (100) and tolerance (28) differ widely; discuss with the investor."])
    portfolio = SimpleNamespace(
        constraints={"name": "Cautious", "score_min": 21, "score_max": 40,
                     "min_equity": min_equity, "max_equity": max_equity,
                     "max_volatility": 0.11, "min_defensive": 0.45, "per_asset_cap": 0.35},
        objective_used="max_sharpe", risk_free_rate=0.0557,
        excluded_sectors=["pharma"], unmatched_exclusions=["Cannabis", "Gambling"],
        snapshot_id="test-snapshot",
        weights={"GOLDBEES.NS": 0.35, "LIQUIDBEES.NS": 0.35, "BANKBEES.NS": 0.30},
        expected_return=0.10, volatility=0.058, sharpe=0.76,
        binding=["GOLDBEES.NS is at the 35% per-asset cap"])
    return assessment, portfolio


def test_contributions_add_up():
    assessment, portfolio = stored_rows()
    r = build_rationale(assessment, portfolio, *market())
    assert abs(sum(c.risk_share for c in r.contributions) - 1) < 1e-9
    assert abs(sum(c.return_contribution for c in r.contributions) - 0.10) < 1e-9
    assert [c.ticker for c in r.contributions][0] in ("GOLDBEES.NS", "LIQUIDBEES.NS")


def test_explains_who_governed_and_the_exclusions():
    assessment, portfolio = stored_rows()
    text = build_rationale(assessment, portfolio, *market()).as_text()
    assert "Tolerance is the lower of the two" in text
    assert "PHARMABEES.NS removed" in text
    assert "Cannabis, Gambling" in text
    assert "differ widely" in text


def test_mentions_horizon_when_it_caps_equity():
    assessment, portfolio = stored_rows(horizon="short", score=80, min_equity=0.26, max_equity=0.30)
    text = build_rationale(assessment, portfolio, *market()).as_text()
    assert "short investment horizon caps equity at 30%" in text


def test_deterministic():
    assessment, portfolio = stored_rows()
    assert build_rationale(assessment, portfolio, *market()) == build_rationale(assessment, portfolio, *market())