from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Rule
from app.schemas.pydantic_schemas import RuleSchema

router = APIRouter()

@router.get("", response_model=List[RuleSchema])
def list_all_rules(db: Session = Depends(get_db)):
    rules = db.query(Rule).all()
    return [RuleSchema.from_orm(r) for r in rules]
