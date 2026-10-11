import numpy as np
import pandas as pd
import pytest

from config.risk_constraints import (
    ASSETS, BUCKETS, DEFENSIVE_CLASSES, PER_ASSET_CAP, BucketConstraints,
)
from optimizer.engine import (
    InfeasiblePortfolioError, class_weight, evaluate_constraints, optimize_portfolio,
)


def synthetic_market():
    """Made-up but plausible inputs, so tests need no network or database."""
    ret = {"equity": 0.13, "gold": 0.10, "debt": 0.072, "cash": 0.066}
    vol = {"equity": 0.18, "gold": 0.13, "debt": 0.04, "cash": 0.005}
    tickers = [a.ticker for a in ASSETS]
    mu, sd = [], []
    for i, a in enumerate(ASSETS):
        bump = 0.01 * i if a.asset_class == "equity" else 0.0
        mu.append(ret[a.asset_class] + bump)
        sd.append(vol[a.asset_class] + bump)
    n = len(ASSETS)
    corr = np.full((n, n), 0.05)
    for i in range(n):
        for j in range(n):
            if ASSETS[i].asset_class == ASSETS[j].asset_class == "equity":
                corr[i, j] = 0.7
    np.fill_diagonal(corr, 1.0)
    cov = np.outer(sd, sd) * corr
    return pd.Series(mu, index=tickers), pd.DataFrame(cov, index=tickers, columns=tickers)


@pytest.mark.parametrize("bucket", BUCKETS, ids=lambda b: b.name)
def test_respects_every_constraint(bucket):
    mu, cov = synthetic_market()
    result = optimize_portfolio(mu, cov, bucket)
    w = pd.Series(result.weights)
    assert abs(w.sum() - 1) < 1e-4
    assert (w >= 0).all() and (w <= PER_ASSET_CAP + 1e-4).all()
    assert class_weight(w, {"equity"}) <= bucket.max_equity + 1e-4
    assert class_weight(w, DEFENSIVE_CLASSES) >= bucket.min_defensive - 1e-4
    assert result.volatility <= bucket.max_volatility + 1e-4


def test_deterministic():
    mu, cov = synthetic_market()
    assert optimize_portfolio(mu, cov, BUCKETS[2]) == optimize_portfolio(mu, cov, BUCKETS[2])


def test_excluded_sector_gets_zero_weight():
    mu, cov = synthetic_market()
    result = optimize_portfolio(mu, cov, BUCKETS[4], excluded_sectors={"banking"})
    assert result.weights["BANKBEES.NS"] == 0


def test_impossible_constraints_raise_readable_error():
    mu, cov = synthetic_market()
    impossible = BucketConstraints("Impossible", 0, 0, 0.0, 0.0001, 0.60, "min_volatility")
    with pytest.raises(InfeasiblePortfolioError):
        optimize_portfolio(mu, cov, impossible)


def test_manual_edit_violations_are_flagged():
    w = pd.Series({a.ticker: 0.0 for a in ASSETS})
    w["NIFTYBEES.NS"] = 1.0
    _, violations = evaluate_constraints(w, 0.18, BUCKETS[0])
    assert violations