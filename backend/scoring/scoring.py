"""
answers -> capacity and tolerance sub-scores -> governing score -> constraints.

WHY two sub-scores: one blended score cannot tell a long-horizon investor who
panics at losses from a short-horizon investor who is fearless. The lower
sub-score governs, because a portfolio must fit both.
Pure functions, no randomness: identical answers always give identical output.
"""
from dataclasses import dataclass, replace

from config.risk_constraints import (
    BUCKETS,
    EQUITY_BAND_HALF_WIDTH,
    EQUITY_TARGET_AT_SCORE_0,
    EQUITY_TARGET_AT_SCORE_100,
    HORIZON_EQUITY_CEILING,
    SUBSCORE_GAP_FOR_REVIEW,
    BucketConstraints,
)
from scoring.questionnaire import (
    CAPACITY_QUESTIONS,
    HORIZON_BY_OPTION,
    HORIZON_QUESTION_ID,
    NO_RISK_ANSWER,
    QUESTION_POINTS,
    QUESTIONNAIRE_VERSION,
    TOLERANCE_QUESTIONS,
    TOP_RETURN_ANSWER,
)


class InvalidAnswersError(ValueError):
    """Answers are incomplete or reference an option that does not exist."""


@dataclass(frozen=True)
class ScoreResult:
    capacity_score: int            # 0-100
    tolerance_score: int           # 0-100
    score: int                     # the lower of the two
    limited_by: str                # "capacity" | "tolerance" | "both"
    horizon: str
    constraints: BucketConstraints # what the optimizer receives
    notes: tuple[str, ...]         # for the rationale and manager review
    questionnaire_version: str


def _validate(answers: dict[int, int]) -> None:
    if set(answers) != set(QUESTION_POINTS):
        missing = sorted(set(QUESTION_POINTS) - set(answers))
        extra = sorted(set(answers) - set(QUESTION_POINTS))
        raise InvalidAnswersError(f"missing questions {missing}, unknown questions {extra}")
    for question_id, option in answers.items():
        if not 0 <= option < len(QUESTION_POINTS[question_id]):
            raise InvalidAnswersError(f"question {question_id} has no option {option}")


def sub_score(answers: dict[int, int], question_ids) -> int:
    """Points for one group of questions, rescaled to 0-100 (rounded half-up,
    in whole-number arithmetic so boundaries never suffer rounding error)."""
    lowest = sum(min(QUESTION_POINTS[q]) for q in question_ids)
    highest = sum(max(QUESTION_POINTS[q]) for q in question_ids)
    raw = sum(QUESTION_POINTS[q][answers[q]] for q in question_ids)
    span = highest - lowest
    return (200 * (raw - lowest) + span) // (2 * span)


def bucket_for_score(score: int) -> BucketConstraints:
    for bucket in BUCKETS:
        if bucket.score_min <= score <= bucket.score_max:
            return bucket
    raise ValueError(f"score {score} is outside 0-100")


def equity_target(score: int) -> float:
    """Straight line from the score-0 target to the score-100 target."""
    step = (EQUITY_TARGET_AT_SCORE_100 - EQUITY_TARGET_AT_SCORE_0) / 100
    return EQUITY_TARGET_AT_SCORE_0 + step * score


def horizon_rule_applies(score: int, horizon: str) -> bool:
    wanted = equity_target(score) + EQUITY_BAND_HALF_WIDTH
    return wanted > HORIZON_EQUITY_CEILING[horizon] + 1e-9


def constraints_for_score(score: int, horizon: str) -> BucketConstraints:
    """Start from the bucket's row (label, volatility cap, defensive minimum,
    objective), then replace its equity limits with the sliding band."""
    bucket = bucket_for_score(score)
    target = equity_target(score)
    low = max(0.0, target - EQUITY_BAND_HALF_WIDTH)
    high = min(1.0, target + EQUITY_BAND_HALF_WIDTH)
    if horizon_rule_applies(score, horizon):
        high = HORIZON_EQUITY_CEILING[horizon]
        low = min(low, max(0.0, high - 2 * EQUITY_BAND_HALF_WIDTH))
    return replace(bucket, min_equity=round(low, 4), max_equity=round(high, 4))


def score_questionnaire(answers: dict[int, int]) -> ScoreResult:
    _validate(answers)
    capacity = sub_score(answers, CAPACITY_QUESTIONS)
    tolerance = sub_score(answers, TOLERANCE_QUESTIONS)
    score = min(capacity, tolerance)
    if capacity == tolerance:
        limited_by = "both"
    else:
        limited_by = "capacity" if capacity < tolerance else "tolerance"
    horizon = HORIZON_BY_OPTION[answers[HORIZON_QUESTION_ID]]

    notes = []
    if horizon_rule_applies(score, horizon):
        notes.append(f"Equity limited to {HORIZON_EQUITY_CEILING[horizon]:.0%} "
                     f"because the investment horizon is {horizon}.")
    if abs(capacity - tolerance) >= SUBSCORE_GAP_FOR_REVIEW:
        notes.append(f"Capacity ({capacity}) and tolerance ({tolerance}) differ "
                     f"widely; discuss with the investor.")
    if (answers[NO_RISK_ANSWER[0]] == NO_RISK_ANSWER[1]
            and answers[TOP_RETURN_ANSWER[0]] == TOP_RETURN_ANSWER[1]):
        notes.append("Expects the highest returns but is unwilling to take any "
                     "risk; clarify with the investor.")

    return ScoreResult(
        capacity_score=capacity,
        tolerance_score=tolerance,
        score=score,
        limited_by=limited_by,
        horizon=horizon,
        constraints=constraints_for_score(score, horizon),
        notes=tuple(notes),
        questionnaire_version=QUESTIONNAIRE_VERSION,
    )