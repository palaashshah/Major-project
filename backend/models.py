from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Date, BigInteger
from sqlalchemy.dialects.postgresql import JSON
from database import Base

'''
models.py describes the database — the actual table columns, types, foreign keys. 
SQLAlchemy reads this to know how to talk to PostgreSQL.
'''
class User(Base):
    __tablename__ = "users"

    id = Column(String(255), primary_key=True)
    name = Column(String(255))
    role = Column(String(50)) # user = investor, manager, admin

class Investor(Base):
    __tablename__ = "investors"

    id = Column(String, primary_key=True)
    name = Column(String)
    demographics = Column(JSON) # flexible: sex, age, city, etc.
    total_aum = Column(Numeric) # assets under management
    investment_horizon = Column(String) # "short", "medium", "long"
    risk_score = Column(String) # "conservative", "moderate", "aggressive"
    preferences_constraints = Column(JSON) # excluded sectors, goals, etc.
    assigned_manager_id = Column(String, ForeignKey("users.id"))

class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(String, primary_key=True)    
    investor_id = Column(String, ForeignKey("investors.id"))
    timestamp = Column(DateTime)
    interaction_type = Column(String) # "call", "email", "meeting"
    notes = Column(String)
    manager_id = Column(String, ForeignKey("users.id"))

class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(String, primary_key=True)
    asset_symbol = Column(String)
    date = Column(Date)
    open_price = Column(Numeric)
    close_price = Column(Numeric)
    high_price = Column(Numeric)
    low_price = Column(Numeric)
    volume = Column(BigInteger)
    data_source = Column(String)