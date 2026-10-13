"""
Points per option, in the same order as src/lib/questions.ts.
WHY: the backend owns scoring, so the frontend sends only
{question_id: option_index} and never a score.
Bump QUESTIONNAIRE_VERSION whenever a question or point value changes.
"""
QUESTIONNAIRE_VERSION = "v2"

QUESTION_POINTS: dict[int, tuple[int, ...]] = {
    4: (3, 6, 9),          # years until withdrawal
    5: (3, 6, 9),          # primary objective
    6: (0, 3, 7, 10),      # reaction to a 20% fall
    7: (3, 9, 15),         # biggest fear
    8: (0, 4, 8, 13),      # risk vs reward
    9: (3, 9, 12),         # knowledge and experience
    10: (2, 4, 7, 10),     # maximum one-year loss
    11: (2, 4, 7, 10),     # return expectation
    12: (3, 5, 7, 9),      # overall approach
    13: (0, 3, 6, 9, 12),  # emergency fund
}

# Capacity = what the investor's situation allows.
CAPACITY_QUESTIONS = (4, 5, 9, 13)
# Tolerance = what the investor's nerves allow.
TOLERANCE_QUESTIONS = (6, 7, 8, 10, 11, 12)

HORIZON_QUESTION_ID = 4
HORIZON_BY_OPTION = ("short", "medium", "long")

# (question_id, option_index) pairs used by the contradiction check.
NO_RISK_ANSWER = (8, 0)        # "not willing to take any risk"
TOP_RETURN_ANSWER = (11, 3)    # highest return expectation