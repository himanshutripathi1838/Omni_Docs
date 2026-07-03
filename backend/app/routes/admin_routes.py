from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.document_model import Document
from app.models.history_model import History
from app.models.user_model import User


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def admin_stats(db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "documents": db.query(Document).count(),
        "processed": db.query(History).filter(History.status == "completed").count(),
        "storage_mode": "local",
    }
