"""
Single source of truth for every tunable number in the recommendation path
(PRD §5.3). WHY: values are provisional and will be tuned from the backtest,
so they must live in one place, never as magic numbers elsewhere.
"""
from dataclasses import dataclass

OBJECTIVES = ("min_volatility", "max_sharpe", "max_return")


@dataclass(frozen=True)
class BucketConstraints:
    name: str
    score_min: int          # inclusive, on the 0-100 normalised scale
    score_max: int          # inclusive
    max_equity: float
    max_volatility: float   # annualised
    min_defensive: float
    objective: str          # one of OBJECTIVES
    min_equity: float = 0.0


# NOTE: CLAUDE.md says min_volatility for Cautious too. That makes Cautious
# provably no riskier than Conservative (looser constraints, same objective),
# which breaks the "risk ordering" success metric. Following PRD §5.3 instead.
BUCKETS = (
    BucketConstraints("Conservative", 0, 20, 0.20, 0.08, 0.60, "min_volatility"),
    BucketConstraints("Cautious", 21, 40, 0.40, 0.11, 0.45, "max_sharpe", min_equity=0.20),
    BucketConstraints("Moderate", 41, 60, 0.60, 0.14, 0.30, "max_sharpe", min_equity=0.40),
    BucketConstraints("Growth", 61, 80, 0.80, 0.18, 0.15, "max_sharpe", min_equity=0.60),
    BucketConstraints("Aggressive", 81, 100, 0.95, 0.22, 0.05, "max_sharpe", min_equity=0.80),
)
PER_ASSET_CAP = 0.35

# sourced figure and cite it in the report from "https://rbi.org.in/scripts/BS_PressReleaseDisplay.aspx?prid=63746"
RISK_FREE_RATE = 0.0557 # RBI 91-day T-bill cut-off yield, Press Release 2026-2027/1268, 7 Oct 2026

EQUITY_CLASS = "equity"
# PRD says "debt + gold". Cash (liquid fund) is counted as defensive here;
# remove "cash" to follow the PRD wording literally.
DEFENSIVE_CLASSES = frozenset({"debt", "gold", "cash"})


@dataclass(frozen=True)
class Asset:
    ticker: str
    asset_class: str        # "equity" | "debt" | "gold" | "cash"
    sector: str | None      # tag used for investor sector exclusions


ASSETS = (
    Asset("NIFTYBEES.NS", "equity", None),
    Asset("JUNIORBEES.NS", "equity", None),
    Asset("BANKBEES.NS", "equity", "banking"),
    Asset("ITBEES.NS", "equity", "it"),
    Asset("PHARMABEES.NS", "equity", "pharma"),
    Asset("GOLDBEES.NS", "gold", None),
    Asset("SETF10GILT.NS", "debt", None),
    Asset("LIQUIDBEES.NS", "cash", None),
)

# --- Sliding equity target -------------------------------------------------
# The score sets the equity share directly, replacing the stepped equity
# limits in BUCKETS (those remain only for the per-bucket preview/backtest).
EQUITY_TARGET_AT_SCORE_0 = 0.10
EQUITY_TARGET_AT_SCORE_100 = 0.90
EQUITY_BAND_HALF_WIDTH = 0.02      # optimizer may sit 2 points either side

# --- Horizon rule ----------------------------------------------------------
# Hard ceiling on equity, whatever the score says.
HORIZON_EQUITY_CEILING = {"short": 0.30, "medium": 0.60, "long": 1.00}

# Flag the profile for manager review when the sub-scores differ this much.
SUBSCORE_GAP_FOR_REVIEW = 40

# --- Drift monitoring ------------------------------------------------------
# Flag a portfolio when any holding moves this far from its approved weight.
DRIFT_THRESHOLD = 0.05