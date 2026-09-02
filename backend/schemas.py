'''
schemas.py describes the API — what data is allowed IN and what goes OUT. 
Pydantic reads this to validate requests.
'''

from pydantic import BaseModel # a high-performance Python library for data validation and settings management. BaseModel is 
                               # the primary class used to define data schemas, ensuring data conforms to specified types and constraints
from typing import Optional # When a field is Optional, it means it's not required — if you don't send it, it just becomes None.
from datetime import datetime

class InvestorCreate(BaseModel):
    # fields the user sends when creating an investor
    # no id (auto generated)
    name: str
    demographics: Optional[dict] = None
    total_aum: Optional[float] = None
    investment_horizon: Optional[str] = None
    risk_score: Optional[str] = None
    preferences_constraints: Optional[dict] = None
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