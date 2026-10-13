"""
Risk scoring endpoints.

WHY: scoring must run in the backend (the frontend sends only answers), and
every submission is stored as an append-only RiskAssessment row so a score
can always be reproduced and audited.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Investor, RiskAssessment
from schemas import RiskAnswers, RiskAssessmentResponse, RiskScoreResponse
from scoring.scoring import InvalidAnswersError, ScoreResult, score_questionnaire
from audit_trail import record_audit

router = APIRouter(tags=["Risk"])


def score_or_422(answers: dict[int, int]) -> ScoreResult:
    """Score the answers; turn a bad submission into a readable 422 error."""
    try:
        return score_questionnaire(answers)
    except InvalidAnswersError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


def result_fields(result: ScoreResult) -> dict:
    """The parts of a ScoreResult that are returned and stored."""
    return {
        "capacity_score": result.capacity_score,
        "tolerance_score": result.tolerance_score,
        "score": result.score,
        "limited_by": result.limited_by,
        "bucket": result.constraints.name,
        "horizon": result.horizon,
        "min_equity": result.constraints.min_equity,
        "max_equity": result.constraints.max_equity,
        "notes": list(result.notes),
        "questionnaire_version": result.questionnaire_version,
    }


def record_assessment(db: Session, investor: Investor, answers: dict[int, int]) -> RiskAssessment:
    """Score the answers, add a RiskAssessment row and update the investor's
    summary fields. The caller commits."""
    result = score_or_422(answers)
    assessment = RiskAssessment(
        id=str(uuid.uuid4()),
        investor_id=investor.id,
        created_at=datetime.now(timezone.utc),
        answers={str(q): option for q, option in answers.items()},
        **result_fields(result),
    )
    db.add(assessment)
    record_audit(db, investor.assigned_manager_id, "assessment.recorded", "investor", investor.id,
                after={"assessment_id": assessment.id, "capacity": result.capacity_score,
                    "tolerance": result.tolerance_score, "score": result.score,
                    "bucket": result.constraints.name})
    investor.risk_score = result.constraints.name      # bucket label, for existing screens
    investor.investment_horizon = result.horizon
    return assessment


@router.post("/risk/score", response_model=RiskScoreResponse)
def preview_score(body: RiskAnswers):
    """Score answers without saving anything (used by the review screen)."""
    return result_fields(score_or_422(body.answers))


@router.post("/investors/{investor_id}/risk-assessments", response_model=RiskAssessmentResponse)
def create_assessment(investor_id: str, body: RiskAnswers, db: Session = Depends(get_db)):
    investor = db.query(Investor).filter(Investor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    assessment = record_assessment(db, investor, body.answers)
    db.commit()
    db.refresh(assessment)
    return assessment


@router.get("/investors/{investor_id}/risk-assessments", response_model=list[RiskAssessmentResponse])
def list_assessments(investor_id: str, db: Session = Depends(get_db)):
    return (
        db.query(RiskAssessment)
        .filter(RiskAssessment.investor_id == investor_id)
        .order_by(RiskAssessment.created_at.desc())
        .all()
    )