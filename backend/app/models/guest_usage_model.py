from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.database.db import Base


class GuestUsage(Base):
    __tablename__ = "guest_usage"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(String(120), unique=True, index=True, nullable=False)
    edit_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
