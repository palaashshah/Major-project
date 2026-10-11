from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import Investor
from schemas import InvestorCreate, InvestorUpdate, InvestorResponse
from routers.risk import record_assessment

router = APIRouter(
    prefix="/investors",  # all routes in this file start with /investors
    tags=["Investors"]    # just groups them nicely in the docs
)

# @router.post("/", response_model=InvestorResponse)
# def create_investor(investor: InvestorCreate, db: Session = Depends(get_db)):
# #                   ↑
# #                   data COMING IN from the form
# #                   no id, just the fields the user filled

#     new_investor = Investor(
#         id=str(uuid.uuid4()), # generate a unique ID automatically
#         **investor.model_dump() # unpacks the schema into a dictionary of fields. You then need to "spread" those fields into the object using **
#     )
#     db.add(new_investor)      # puts new investor in the basket
#     db.commit()               # saves to PostgreSQL
#     db.refresh(new_investor)  # get the receipt, reload the item with what DB actually saved
#     return new_investor
# #   ↑
# #   response_model=InvestorResponse shapes this on the way OUT
# #   now has id, all fields

@router.post("/", response_model=InvestorResponse)
def create_investor(investor: InvestorCreate, db: Session = Depends(get_db)):
    data = investor.model_dump()
    answers = data.pop("risk_answers", None)    # not a column on Investor

    new_investor = Investor(id=str(uuid.uuid4()), **data)
    db.add(new_investor)

    if answers is not None:
        db.flush()                              # insert the investor first, so the assessment can point to it
        record_assessment(db, new_investor, answers)   # overwrites risk_score and horizon with server values

    db.commit()
    db.refresh(new_investor)
    return new_investor

@router.get("/", response_model=list[InvestorResponse])
def get_all_investors(db: Session = Depends(get_db)):
    return db.query(Investor).all()

@router.get("/{investor_id}", response_model=InvestorResponse)
def get_investor(investor_id: str, db: Session = Depends(get_db)):
    investor = db.query(Investor).filter(Investor.id == investor_id).first()

    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    return investor

@router.put("/{investor_id}", response_model=InvestorResponse)
def update_investor(updates: InvestorUpdate,investor_id: str, db: Session = Depends(get_db)):

    investor = db.query(Investor).filter(Investor.id == investor_id).first()
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(investor, field, value)

    db.commit()
    db.refresh(investor)

    return investor


@router.delete("/{investor_id}")
def delete_investor(investor_id: str, db: Session = Depends(get_db)):
    investor = db.query(Investor).filter(Investor.id == investor_id).first()

    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    db.delete(investor)
    db.commit()

    return {"message": f"Investor {investor_id} deleted successfully"}