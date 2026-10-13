"""
Read-only reference endpoints.

WHY: the frontend must not keep its own copy of the ETF list, the limits or
the questionnaire's shape. It reads them here, so there is one source of truth.
"""
from fastapi import APIRouter

from config.risk_constraints import (
    ASSETS,
    BUCKETS,
    DRIFT_THRESHOLD,
    EQUITY_BAND_HALF_WIDTH,
    EQUITY_TARGET_AT_SCORE_0,
    EQUITY_TARGET_AT_SCORE_100,
    HORIZON_EQUITY_CEILING,
    PER_ASSET_CAP,
    RISK_FREE_RATE,
)
from optimizer.engine import cap_for
from scoring.questionnaire import (
    CAPACITY_QUESTIONS,
    HORIZON_BY_OPTION,
    HORIZON_QUESTION_ID,
    QUESTION_POINTS,
    QUESTIONNAIRE_VERSION,
)

router = APIRouter(tags=["Reference"])


@router.get("/universe")
def universe():
    """The instruments and every limit the optimizer currently applies."""
    return {
        "assets": [
            {"ticker": a.ticker, "asset_class": a.asset_class, "sector": a.sector, "cap": cap_for(a.ticker)}
            for a in ASSETS
        ],
        "excludable_sectors": sorted({a.sector for a in ASSETS if a.sector}),
        "per_asset_cap": PER_ASSET_CAP,
        "risk_free_rate": RISK_FREE_RATE,
        "drift_threshold": DRIFT_THRESHOLD,
        "equity_target": {
            "at_score_0": EQUITY_TARGET_AT_SCORE_0,
            "at_score_100": EQUITY_TARGET_AT_SCORE_100,
            "band_half_width": EQUITY_BAND_HALF_WIDTH,
        },
        "horizon_equity_ceiling": HORIZON_EQUITY_CEILING,
        "buckets": [
            {"name": b.name, "score_min": b.score_min, "score_max": b.score_max,
             "max_volatility": b.max_volatility, "min_defensive": b.min_defensive,
             "objective": b.objective}
            for b in BUCKETS
        ],
    }


@router.get("/questionnaire/meta")
def questionnaire_meta():
    """The questionnaire's shape, so the frontend can confirm it matches."""
    return {
        "version": QUESTIONNAIRE_VERSION,
        "questions": [
            {"id": question_id, "options": len(points),
             "group": "capacity" if question_id in CAPACITY_QUESTIONS else "tolerance"}
            for question_id, points in QUESTION_POINTS.items()
        ],
        "horizon_question_id": HORIZON_QUESTION_ID,
        "horizon_by_option": list(HORIZON_BY_OPTION),
    }