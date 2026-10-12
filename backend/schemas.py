'''
schemas.py describes the API — what data is allowed IN and what goes OUT. 
Pydantic reads this to validate requests.
'''

from pydantic import BaseModel # a high-performance Python library for data validation and settings management. BaseModel is 
                               # the primary class used to define data schemas, ensuring data conforms to specified types and constraints
from typing import Literal, Optional # When a field is Optional, it means it's not required — if you don't send it, it just becomes None.
from datetime import datetime
from uuid import UUID
from datetime import date

class InvestorCreate(BaseModel):
    # fields the user sends when creating an investor
    # no id (auto generated)
    name: str
    demographics: Optional[dict] = None
    total_aum: Optional[float] = None
    investment_horizon: Optional[str] = None
    risk_score: Optional[str] = None
    preferences_constraints: Optional[dict] = None
    risk_answers: Optional[dict[int, int]] = None   # {question_id: option_index}; scored by the server
    assigned_manager_id: str

class InvestorUpdate(BaseModel):
    # fields that are updated after creating the investor
    name: Optional[str] = None
    demographics: Optional[dict] = None
    total_aum: Optional[float] = None
    investment_horizon: Optional[str] = None
    risk_score: Optional[str] = None
    preferences_constraints: Optional[dict] = None
    assigned_manager_id: Optional[str] = None
    
class InvestorResponse(BaseModel):
    # fields that are sent to the frontend when requested
    id: str
    name: str
    demographics: Optional[dict] = None
    total_aum: Optional[float] = None
    investment_horizon: Optional[str] = None
    risk_score: Optional[str] = None
    preferences_constraints: Optional[dict] = None
    assigned_manager_id: str

    class Config:
        from_attributes = True
    '''
    This tells Pydantic it can read SQLAlchemy objects directly. Without it, when 
    QLAlchemy returns an Investor object from the DB, Pydantic wouldn't know how to read it.
    When your route fetches an investor from the DB, SQLAlchemy returns an Investor object. 
    But Pydantic expects a dictionary by default.
    '''

class InteractionCreate(BaseModel):
    # what the manager sends
    investor_id: str
    timestamp: Optional[datetime] = None
    interaction_type: Optional[str] = None
    notes: Optional[str] = None
    manager_id: str

class InteractionUpdate(BaseModel):
    # what can be edited after the fact
    investor_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    interaction_type: Optional[str] = None
    notes: Optional[str] = None
    manager_id: Optional[str] = None

class InteractionResponse(BaseModel):
    # what is sent to the frontend
    id: str
    investor_id: str
    timestamp: Optional[datetime] = None
    interaction_type: Optional[str] = None
    notes: Optional[str] = None
    manager_id: str

    class Config:
        from_attributes = True
        # is you telling Pydantic: "Hey, if someone hands you a SQLAlchemy object instead of a dict, you're allowed to read its attributes directly."

class RiskAnswers(BaseModel):
    # what the frontend sends: which option was picked for each question
    answers: dict[int, int]

class RiskScoreResponse(BaseModel):
    # what the backend sends back after scoring
    capacity_score: int
    tolerance_score: int
    score: int
    limited_by: str
    bucket: str
    horizon: str
    min_equity: float
    max_equity: float
    notes: list[str]
    questionnaire_version: str

class RiskAssessmentResponse(RiskScoreResponse):
    # a saved assessment: the score plus who, when and the raw answers
    id: str
    investor_id: str
    created_at: datetime
    answers: dict

    class Config:
        from_attributes = True

class OptimizeRequest(BaseModel):
    investor_id: str
    snapshot_id: Optional[UUID] = None      # leave out to use the newest snapshot
    requested_by: Optional[str] = None      # manager id; defaults to the assigned manager

class MetricsRequest(BaseModel):
    investor_id: str
    weights: dict[str, float]               # {"GOLDBEES.NS": 0.35, ...}
    snapshot_id: Optional[UUID] = None

class MetricsResponse(BaseModel):
    expected_return: float
    volatility: float
    sharpe: float
    binding: list[str]
    violations: list[str]

class PortfolioResponse(BaseModel):
    id: str
    investor_id: str
    assessment_id: str
    snapshot_id: UUID
    created_at: datetime
    created_by: Optional[str] = None
    status: str
    constraints: dict
    excluded_sectors: list[str]
    unmatched_exclusions: list[str]
    risk_free_rate: float
    objective_used: str
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float
    binding: list[str]

    class Config:
        from_attributes = True

class ContributionResponse(BaseModel):
    ticker: str
    asset_class: str
    weight: float
    return_contribution: float
    risk_share: float

class RationaleResponse(BaseModel):
    portfolio_id: str
    summary: str
    profile: list[str]
    rules: list[str]
    binding: list[str]
    contributions: list[ContributionResponse]
    notes: list[str]
    disclaimer: str
    text: str            # the whole explanation as one block

class ManagerDecisionRequest(BaseModel):
    decision: Literal["approved", "rejected"]
    decided_by: str                        # manager id
    reason: Optional[str] = None           # required when rejecting

class ClientDecisionRequest(BaseModel):
    decision: Literal["accepted", "declined"]
    recorded_by: str                       # the manager logging the client's answer
    notes: Optional[str] = None
    amount: Optional[float] = None         # invested amount; defaults to the investor's total_aum

class PortfolioDecisionResponse(BaseModel):
    id: str
    portfolio_id: str
    timestamp: datetime
    actor: str
    decision: str
    reason: Optional[str] = None
    recorded_by: str
    amount: Optional[float] = None

    class Config:
        from_attributes = True

class HoldingValuationResponse(BaseModel):
    ticker: str
    target_weight: float
    start_price: float
    latest_price: float
    value: float
    current_weight: float
    drift: float
    breached: bool
    basis: str                  # "price" or "accrual"

class ValuationResponse(BaseModel):
    portfolio_id: str
    investor_id: str
    hypothetical: bool          # true when an invested_on date was supplied
    start_date: date
    as_of_date: date
    amount: float
    current_value: float
    gain: float
    gain_pct: float
    drift_threshold: float
    rebalancing_suggested: bool
    cash_rate: Optional[float] = None   # yearly rate used to accrue cash holdings
    holdings: list[HoldingValuationResponse]

class AdjustRequest(BaseModel):
    weights: dict[str, float]      # {"GOLDBEES.NS": 0.33, ...}; must add up to 1
    adjusted_by: str               # manager id
    reason: str                    # why the weights were changed

class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: str
    reason: Optional[str] = None
    before: Optional[dict] = None
    after: Optional[dict] = None

    class Config:
        from_attributes = True