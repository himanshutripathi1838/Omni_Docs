from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.history_model import History
from app.schemas.document_schema import HistoryCreate, HistoryOut


router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[HistoryOut])
def get_history(db: Session = Depends(get_db)):
    return db.query(History).order_by(History.created_at.desc()).limit(100).all()


@router.post("", response_model=HistoryOut)
def create_history(payload: HistoryCreate, db: Session = Depends(get_db)):
    history = History(**payload.model_dump())
    db.add(history)
    db.commit()
    db.refresh(history)
    return history
