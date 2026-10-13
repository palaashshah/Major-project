import pytest

from config.risk_constraints import HORIZON_EQUITY_CEILING
from scoring.questionnaire import (
    CAPACITY_QUESTIONS, QUESTION_POINTS, TOLERANCE_QUESTIONS,
)
from scoring.scoring import (
    InvalidAnswersError, bucket_for_score, constraints_for_score, score_questionnaire,
)

LOWEST = {q: 0 for q in QUESTION_POINTS}
HIGHEST = {q: len(p) - 1 for q, p in QUESTION_POINTS.items()}


def test_every_question_is_in_exactly_one_group():
    assert sorted(CAPACITY_QUESTIONS + TOLERANCE_QUESTIONS) == sorted(QUESTION_POINTS)


def test_extremes():
    low, high = score_questionnaire(LOWEST), score_questionnaire(HIGHEST)
    assert (low.score, low.constraints.name) == (0, "Conservative")
    assert (high.score, high.constraints.name) == (100, "Aggressive")


def test_deterministic():
    assert score_questionnaire(HIGHEST) == score_questionnaire(dict(HIGHEST))


def test_lower_subscore_governs():
    brave_situation_nervous_person = {**HIGHEST, **{q: 0 for q in TOLERANCE_QUESTIONS}}
    r = score_questionnaire(brave_situation_nervous_person)
    assert (r.capacity_score, r.tolerance_score, r.score) == (100, 0, 0)
    assert r.limited_by == "tolerance"


@pytest.mark.parametrize("score,name", [
    (0, "Conservative"), (20, "Conservative"), (21, "Cautious"), (40, "Cautious"),
    (41, "Moderate"), (60, "Moderate"), (61, "Growth"), (80, "Growth"),
    (81, "Aggressive"), (100, "Aggressive"),
])
def test_bucket_boundaries(score, name):
    assert bucket_for_score(score).name == name


def test_equity_rises_with_score():
    ceilings = [constraints_for_score(s, "long").max_equity for s in range(101)]
    assert ceilings == sorted(ceilings) and ceilings[0] < ceilings[-1]


def test_short_horizon_caps_equity():
    c = constraints_for_score(100, "short")
    assert c.max_equity == HORIZON_EQUITY_CEILING["short"]


def test_limits_are_consistent_for_every_score_and_horizon():
    for horizon in HORIZON_EQUITY_CEILING:
        for score in range(101):
            c = constraints_for_score(score, horizon)
            assert 0 <= c.min_equity <= c.max_equity <= 1
            assert 1 - c.max_equity >= c.min_defensive  # room left for defensive


def test_contradiction_is_noted():
    r = score_questionnaire({**LOWEST, 11: 3})
    assert any("unwilling" in note for note in r.notes)


def test_riskier_option_never_scores_lower():
    for points in QUESTION_POINTS.values():
        assert list(points) == sorted(points)


def test_rejects_missing_and_invalid_answers():
    incomplete = dict(LOWEST)
    incomplete.pop(4)
    with pytest.raises(InvalidAnswersError):
        score_questionnaire(incomplete)
    with pytest.raises(InvalidAnswersError):
        score_questionnaire({**LOWEST, 5: 99})