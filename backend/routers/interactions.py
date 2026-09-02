from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
from typing import Optional

from database import get_db
from models import Interaction 
from schemas import InteractionCreate, InteractionUpdate, InteractionResponse

router = APIRouter(
    prefix="/interactions",  
    tags=["Interactions"]    
)

@router.post("/", response_model=InteractionResponse)
#                   ↑
#                   InteractionCreate is what comes IN. InteractionResponse is what goes OUT.
def create_interactions(interaction: InteractionCreate, db: Session= Depends(get_db)):

    new_interaction = Interaction(
        id=str(uuid.uuid4()), 
        **interaction.model_dump() 
    )

    if not new_interaction.timestamp:
        new_interaction.timestamp = datetime.utcnow()
    db.add(new_interaction)     
    db.commit()               
    db.refresh(new_interaction)
    return new_interaction

@router.get("/", response_model=list[InteractionResponse])
def get_interactions(investor_id: Optional[str] = None, db: Session = Depends(get_db)):
    # Optional[str] = None means investor_id is no longer required
    # if investor_id is provided → filter by it
    # if not provided → return everything

    if investor_id:
        # filter by investor
        interactions = db.query(Interaction).filter(Interaction.investor_id == investor_id).all()
        # db query => Interaction, where Interaction.investor_id == {investor_id}
    else:
        # no filter — return all interactions
        interactions = db.query(Interaction).all()

    if not interactions:
        raise HTTPException(status_code=404, detail="No interactions found")
    
    return interactions