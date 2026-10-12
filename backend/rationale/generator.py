"""
Rule-derived explanation for a saved portfolio (PRD 5.5).

WHY: explainability must be template-based and deterministic, with no ML.
Every sentence is filled from values stored with the assessment and the
portfolio, so the same run always yields the same text.
Pure function: no database access here; the router loads the inputs.
"""
from dataclasses import dataclass

import pandas as pd

from config.risk_constraints import ASSETS, HORIZON_EQUITY_CEILING
from scoring.scoring import equity_target, horizon_rule_applies

ASSET_CLASS = {a.ticker: a.asset_class for a in ASSETS}

DISCLAIMER = ("Expected return and risk are estimates from historical data. "
              "They are not forecasts or guarantees.")

OBJECTIVE_TEXT = {
    "max_sharpe": ("Within those limits the optimizer chose the mix with the highest return "
                   "per unit of risk (maximum Sharpe ratio), using a risk-free rate of {rf:.2%}."),
    "min_volatility": "Within those limits the optimizer chose the mix with the lowest volatility.",
    "max_return_at_volatility_cap": ("The best risk-adjusted mix exceeded the volatility limit, "
                                     "so the optimizer chose the highest-return mix inside it."),
    "manual_adjustment": ("The weights were set by the manager, adjusting the optimizer's "
                          "proposal. They were checked against the same limits.")
}


@dataclass(frozen=True)
class Contribution:
    ticker: str
    asset_class: str
    weight: float
    return_contribution: float   # weight x average return; these sum to the expected return
    risk_share: float            # fraction of portfolio variance; these sum to 1


def _risk_text(share: float) -> str:
    """Wording for a holding's share of portfolio risk."""
    if share <= -0.005:
        return f"lowers the risk by {abs(share):.0%}"
    if share < 0.005:
        return "almost none of the risk"
    return f"{share:.0%} of the risk"

@dataclass(frozen=True)
class Rationale:
    summary: str
    profile: list[str]
    rules: list[str]
    binding: list[str]
    contributions: list[Contribution]
    notes: list[str]
    disclaimer: str

    def as_text(self) -> str:
        """The whole explanation as one block of text, for the PDF and the portal."""
        lines = [self.summary, "", "Investor profile"]
        lines += [f"- {s}" for s in self.profile]
        lines += ["", "Rules applied"] + [f"- {s}" for s in self.rules]
        lines += ["", "Limits that shaped the result"] + [f"- {s}" for s in self.binding]
        lines += ["", "What each holding contributes"]
        for c in self.contributions:
            lines.append(
                f"- {c.ticker} ({c.asset_class}): {c.weight:.1%} of the portfolio, "
                f"{c.return_contribution * 100:.2f} points of expected return, "
                f"{_risk_text(c.risk_share)}")
        if self.notes:
            lines += ["", "Notes for review"] + [f"- {s}" for s in self.notes]
        lines += ["", self.disclaimer]
        return "\n".join(lines)


def _profile_lines(assessment, constraints: dict) -> list[str]:
    lines = [f"Risk capacity scored {assessment.capacity_score} and risk tolerance scored "
             f"{assessment.tolerance_score}, each out of 100."]
    if assessment.limited_by == "both":
        lines.append(f"The two are equal, so the risk score is {assessment.score}.")
    else:
        lines.append(f"{assessment.limited_by.capitalize()} is the lower of the two, "
                     f"so it sets the risk score of {assessment.score}.")
    lines.append(f"A score of {assessment.score} falls in the {constraints['name']} bucket "
                 f"({constraints['score_min']} to {constraints['score_max']}).")
    return lines


def _rule_lines(assessment, portfolio) -> list[str]:
    c = portfolio.constraints
    target = equity_target(assessment.score)
    band = f"{c['min_equity']:.1%} to {c['max_equity']:.1%}"
    lines = []

    if horizon_rule_applies(assessment.score, assessment.horizon):
        ceiling = HORIZON_EQUITY_CEILING[assessment.horizon]
        lines.append(f"The score alone would target {target:.1%} in equity, but the "
                     f"{assessment.horizon} investment horizon caps equity at {ceiling:.0%}. "
                     f"The optimizer was allowed {band}.")
    else:
        lines.append(f"The score sets an equity target of {target:.1%}. "
                     f"The optimizer was allowed {band}.")

    lines.append(f"Volatility could not exceed {c['max_volatility']:.0%}, at least "
                 f"{c['min_defensive']:.0%} had to be in defensive assets, and no single "
                 f"instrument could exceed {c['per_asset_cap']:.0%}.")

    template = OBJECTIVE_TEXT.get(portfolio.objective_used)
    if template:
        lines.append(template.format(rf=portfolio.risk_free_rate))
    else:
        lines.append(f"Objective used: {portfolio.objective_used}.")

    if portfolio.excluded_sectors:
        removed = [asset.ticker for asset in ASSETS if asset.sector in portfolio.excluded_sectors]
        lines.append(f"Excluded at the investor's request: {', '.join(portfolio.excluded_sectors)} "
                     f"({', '.join(removed)} removed).")
    if portfolio.unmatched_exclusions:
        lines.append("Recorded but not applied, because no instrument in the universe matches: "
                     f"{', '.join(portfolio.unmatched_exclusions)}.")

    lines.append(f"Return and risk estimates come from data snapshot {portfolio.snapshot_id}.")
    return lines


def _contributions(weights: dict, mu: pd.Series, cov: pd.DataFrame) -> list[Contribution]:
    w = pd.Series(weights, dtype=float).reindex(mu.index).fillna(0.0).to_numpy()
    sigma = cov.loc[mu.index, mu.index].to_numpy()
    variance = float(w @ sigma @ w)
    marginal = sigma @ w          # how much each ETF adds to variance per unit of weight

    rows = []
    for i, ticker in enumerate(mu.index):
        if w[i] <= 0:
            continue
        rows.append(Contribution(
            ticker=ticker,
            asset_class=ASSET_CLASS.get(ticker, "unknown"),
            weight=float(w[i]),
            return_contribution=float(w[i] * mu.iloc[i]),
            risk_share=float(w[i] * marginal[i] / variance) if variance > 0 else 0.0,
        ))
    rows.sort(key=lambda r: (-r.weight, r.ticker))   # biggest holding first; ticker breaks ties
    return rows


def build_rationale(assessment, portfolio, mu: pd.Series, cov: pd.DataFrame) -> Rationale:
    """assessment and portfolio are the stored rows (or any objects with the
    same attribute names, which keeps this easy to test)."""
    binding = list(portfolio.binding) or [
        "No limit was binding: the chosen mix sat inside every limit."]
    return Rationale(
        summary=(f"Recommended portfolio: expected return {portfolio.expected_return:.2%}, "
                 f"volatility {portfolio.volatility:.2%}, Sharpe ratio {portfolio.sharpe:.2f}."),
        profile=_profile_lines(assessment, portfolio.constraints),
        rules=_rule_lines(assessment, portfolio),
        binding=binding,
        contributions=_contributions(portfolio.weights, mu, cov),
        notes=list(assessment.notes or []),
        disclaimer=DISCLAIMER,
    )