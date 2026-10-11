import uuid
from sqlalchemy import Column, String, ForeignKey, Numeric, DateTime, Date, BigInteger, Float, ARRAY, Integer
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship
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

# -------------------------------------------------------------
# MARKET DATA SNAPSHOT MODELS (Stage 4)
# -------------------------------------------------------------

class DataSnapshot(Base):
    __tablename__ = "data_snapshots"

    snapshot_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, nullable=False)
    ticker_list = Column(ARRAY(String), nullable=False)

    means = relationship("AssetMean", back_populates="snapshot", cascade="all, delete-orphan")
    covariances = relationship("AssetCovariance", back_populates="snapshot", cascade="all, delete-orphan")

class AssetMean(Base):
    __tablename__ = "asset_means"

    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("data_snapshots.snapshot_id"), primary_key=True)
    ticker = Column(String, primary_key=True)
    mean_return = Column(Float, nullable=False)

    snapshot = relationship("DataSnapshot", back_populates="means")

class AssetCovariance(Base):
    __tablename__ = "asset_covariances"

    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("data_snapshots.snapshot_id"), primary_key=True)
    ticker_i = Column(String, primary_key=True)
    ticker_j = Column(String, primary_key=True)
    cov_value = Column(Float, nullable=False)

    snapshot = relationship("DataSnapshot", back_populates="covariances")

# -------------------------------------------------------------
# RISK ASSESSMENTS
# -------------------------------------------------------------
class RiskAssessment(Base):
    """One questionnaire submission and its score. Rows are only ever added,
    never edited, so the table is the audit history of an investor's profile."""
    __tablename__ = "risk_assessments"

    id = Column(String, primary_key=True)
    investor_id = Column(String, ForeignKey("investors.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False)
    questionnaire_version = Column(String, nullable=False)
    answers = Column(JSON, nullable=False)          # {"4": 1, "5": 0, ...}
    capacity_score = Column(Integer, nullable=False)
    tolerance_score = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)         # the lower of the two
    limited_by = Column(String, nullable=False)     # capacity | tolerance | both
    bucket = Column(String, nullable=False)
    horizon = Column(String, nullable=False)
    min_equity = Column(Float, nullable=False)
    max_equity = Column(Float, nullable=False)
    notes = Column(JSON, nullable=False)            # list of strings

# -------------------------------------------------------------
# PORTFOLIOS AND AUDIT LOG
# -------------------------------------------------------------
class Portfolio(Base):
    """One optimizer run for one investor. Stores everything needed to
    reproduce it: the assessment, the data snapshot, the constraints and
    the risk-free rate. Rows are added, never overwritten."""
    __tablename__ = "portfolios"

    id = Column(String, primary_key=True)
    investor_id = Column(String, ForeignKey("investors.id"), nullable=False, index=True)
    assessment_id = Column(String, ForeignKey("risk_assessments.id"), nullable=False)
    snapshot_id = Column(UUID(as_uuid=True), ForeignKey("data_snapshots.snapshot_id"), nullable=False)
    created_at = Column(DateTime, nullable=False)
    created_by = Column(String)
    status = Column(String, nullable=False)            # proposed | approved | rejected
    constraints = Column(JSON, nullable=False)         # the limits the optimizer was given
    excluded_sectors = Column(JSON, nullable=False)    # exclusions that were applied
    unmatched_exclusions = Column(JSON, nullable=False)  # requested, but no ETF matches
    risk_free_rate = Column(Float, nullable=False)
    objective_used = Column(String, nullable=False)
    weights = Column(JSON, nullable=False)             # {"GOLDBEES.NS": 0.35, ...}
    expected_return = Column(Float, nullable=False)
    volatility = Column(Float, nullable=False)
    sharpe = Column(Float, nullable=False)
    binding = Column(JSON, nullable=False)             # rules the portfolio sits exactly on


class AuditLog(Base):
    """Append-only record of who did what and when."""
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    user_id = Column(String)
    action = Column(String, nullable=False)            # e.g. "portfolio.optimized"
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    reason = Column(String)
    before = Column(JSON)
    after = Column(JSON)