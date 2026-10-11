"""
(mu, cov, bucket, exclusions) -> weights + metrics + binding constraints.

WHY: weights are always computed by PyPortfolioOpt inside the bucket's
constraints, never looked up. No DB, network or randomness in this module.
portfolio_metrics() and evaluate_constraints() are also what the manual
weight-edit endpoint must call (PRD §5.6: recompute live, flag violations).
"""
from dataclasses import dataclass

import cvxpy as cp
import numpy as np
import pandas as pd
from pypfopt.efficient_frontier import EfficientFrontier
from pypfopt.exceptions import OptimizationError

from config.risk_constraints import (
    ASSETS,
    DEFENSIVE_CLASSES,
    EQUITY_CLASS,
    OBJECTIVES,
    PER_ASSET_CAP,
    RISK_FREE_RATE,
    BucketConstraints,
)

TOL = 1e-4  # numerical slack when comparing against a limit
ASSET_CLASS = {a.ticker: a.asset_class for a in ASSETS}
ASSET_SECTOR = {a.ticker: a.sector for a in ASSETS}


class InfeasiblePortfolioError(Exception):
    """No portfolio satisfies the constraints. Message is safe to show a manager."""


@dataclass(frozen=True)
class PortfolioResult:
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float
    risk_free_rate: float
    objective_used: str
    binding: list[str]       # input for the rationale generator


def portfolio_metrics(weights: pd.Series, mu: pd.Series, cov: pd.DataFrame, rf: float):
    """Expected return, volatility and Sharpe ratio for any weight vector."""
    w = weights.reindex(mu.index).fillna(0.0).to_numpy()
    ret = float(w @ mu.to_numpy()) # return
    vol = float(np.sqrt(w @ cov.loc[mu.index, mu.index].to_numpy() @ w)) # volatility
    sharpe = (ret - rf) / vol if vol > 0 else 0.0 
    return ret, vol, sharpe


def class_weight(weights: pd.Series, classes) -> float:
    return float(sum(w for t, w in weights.items() if ASSET_CLASS.get(t) in classes))


def evaluate_constraints(weights, volatility, bucket, excluded_sectors=frozenset()):
    """Return (binding, violations) as human-readable strings. Used for both
    optimizer output and manual edits, so a violating portfolio is never
    accepted silently."""
    binding, violations = [], []

    if abs(float(weights.sum()) - 1.0) > TOL:
        violations.append(f"Weights sum to {weights.sum():.2%}, not 100%")
    for ticker, w in weights.items():
        if w < -TOL:
            violations.append(f"{ticker} has a negative weight")
        if w > PER_ASSET_CAP + TOL:
            violations.append(f"{ticker} at {w:.1%} exceeds the {PER_ASSET_CAP:.0%} per-asset cap")
        elif w > PER_ASSET_CAP - TOL:
            binding.append(f"{ticker} is at the {PER_ASSET_CAP:.0%} per-asset cap")
        if w > TOL and ASSET_SECTOR.get(ticker) in excluded_sectors:
            violations.append(f"{ticker} is in an excluded sector ({ASSET_SECTOR[ticker]})")

        # Equity: upper limit
    equity = class_weight(weights, {EQUITY_CLASS})
    if equity > bucket.max_equity + TOL:
        violations.append(f"Equity {equity:.1%} exceeds the {bucket.max_equity:.1%} limit for {bucket.name}")
    elif equity > bucket.max_equity - TOL:
        binding.append(f"Equity capped at {bucket.max_equity:.1%} ({bucket.name})")

    # Equity: lower limit (the "band" that keeps buckets distinct)
    if equity < bucket.min_equity - TOL:
        violations.append(f"Equity {equity:.1%} is below the {bucket.min_equity:.1%} minimum for {bucket.name}")
    elif bucket.min_equity > 0 and equity < bucket.min_equity + TOL:
        binding.append(f"Equity held at the {bucket.min_equity:.1%} minimum ({bucket.name})")

    # Defensive: lower limit
    defensive = class_weight(weights, DEFENSIVE_CLASSES)
    if defensive < bucket.min_defensive - TOL:
        violations.append(f"Defensive {defensive:.1%} is below the {bucket.min_defensive:.0%} minimum for {bucket.name}")
    elif defensive < bucket.min_defensive + TOL:
        binding.append(f"Defensive assets held at the {bucket.min_defensive:.0%} minimum ({bucket.name})")

    # Volatility: upper limit
    if volatility > bucket.max_volatility + TOL:
        violations.append(f"Volatility {volatility:.1%} exceeds the {bucket.max_volatility:.0%} limit for {bucket.name}")
    elif volatility > bucket.max_volatility - TOL:
        binding.append(f"Volatility held at the {bucket.max_volatility:.0%} limit ({bucket.name})")

    return binding, violations


def _precheck(allowed, bucket):
    """Catch structural infeasibility with a readable reason before solving."""
    n_equity = sum(ASSET_CLASS[t] == EQUITY_CLASS for t in allowed)
    n_non_equity = len(allowed) - n_equity
    n_defensive = sum(ASSET_CLASS[t] in DEFENSIVE_CLASSES for t in allowed)

    if len(allowed) * PER_ASSET_CAP < 1 - TOL:
        raise InfeasiblePortfolioError(
            f"Only {len(allowed)} instruments remain after exclusions; at "
            f"{PER_ASSET_CAP:.0%} each they cannot reach 100%.")
    if 1 - n_non_equity * PER_ASSET_CAP > bucket.max_equity + TOL:
        raise InfeasiblePortfolioError(
            f"Too few non-equity instruments to keep equity within {bucket.max_equity:.0%}.")
    if n_defensive * PER_ASSET_CAP < bucket.min_defensive - TOL:
        raise InfeasiblePortfolioError(
            f"Too few defensive instruments to reach the {bucket.min_defensive:.0%} minimum.")
    if n_equity * PER_ASSET_CAP < bucket.min_equity - TOL:
        raise InfeasiblePortfolioError(
            f"Too few equity instruments to reach the {bucket.min_equity:.0%} minimum for {bucket.name}.")


def optimize_portfolio(mu, cov, bucket: BucketConstraints,
                       excluded_sectors=frozenset(), rf: float = RISK_FREE_RATE) -> PortfolioResult:
    if bucket.objective not in OBJECTIVES:
        raise ValueError(f"unknown objective {bucket.objective!r}")
    unknown = [t for t in mu.index if t not in ASSET_CLASS]
    if unknown:
        raise ValueError(f"snapshot tickers missing from config ASSETS: {unknown}")

    # Exclusions are zero-weight constraints: drop the assets, re-add as 0 later.
    allowed = [t for t in mu.index if ASSET_SECTOR[t] not in excluded_sectors]
    _precheck(allowed, bucket)
    mu_a, cov_a = mu.loc[allowed], cov.loc[allowed, allowed]
    is_equity = [ASSET_CLASS[t] == EQUITY_CLASS for t in allowed]
    is_defensive = [ASSET_CLASS[t] in DEFENSIVE_CLASSES for t in allowed]

    def build():
        # A solved EfficientFrontier cannot be reused, so build fresh each time.
        ef = EfficientFrontier(mu_a, cov_a, weight_bounds=(0, PER_ASSET_CAP))
        if any(is_equity):
            ef.add_constraint(lambda w: cp.sum(w[is_equity]) <= bucket.max_equity)
        if any(is_equity) and bucket.min_equity > 0:
            ef.add_constraint(lambda w: cp.sum(w[is_equity]) >= bucket.min_equity)
        if any(is_defensive) and bucket.min_defensive > 0:
            ef.add_constraint(lambda w: cp.sum(w[is_defensive]) >= bucket.min_defensive)
        return ef

    try:
        ef, objective_used = None, bucket.objective
        if bucket.objective == "min_volatility":
            ef = build()
            ef.min_volatility()
        elif bucket.objective == "max_sharpe":
            ef = build()
            ef.max_sharpe(risk_free_rate=rf)
            _, vol, _ = portfolio_metrics(pd.Series(ef.clean_weights()), mu_a, cov_a, rf)
            if vol > bucket.max_volatility + TOL:
                ef = None  # tangency portfolio is too risky for this bucket
        if ef is None:
            # Best return whose volatility stays within the bucket's cap. When
            # the tangency portfolio breaches the cap, this frontier point is
            # also the highest-Sharpe portfolio that respects it.
            ef = build()
            ef.efficient_risk(target_volatility=bucket.max_volatility)
            objective_used = "max_return_at_volatility_cap"
    except (OptimizationError, ValueError, cp.error.SolverError) as exc:
        raise InfeasiblePortfolioError(
            f"No portfolio satisfies the {bucket.name} constraints: {exc}") from exc

    weights = pd.Series(ef.clean_weights(), dtype=float).reindex(mu.index).fillna(0.0)
    weights = (weights / weights.sum()).round(6)
    ret, vol, sharpe = portfolio_metrics(weights, mu, cov, rf)
    binding, violations = evaluate_constraints(weights, vol, bucket, excluded_sectors)
    if violations:
        raise InfeasiblePortfolioError("; ".join(violations))

    return PortfolioResult(weights.to_dict(), ret, vol, sharpe, rf, objective_used, binding)