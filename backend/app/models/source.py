from sqlalchemy import Column, String, Boolean
from app.db.base import Base

class Source(Base):
    __tablename__ = "sources"

    source_id = Column(String(30), primary_key=True, index=True)
    source_name = Column(String(100), nullable=False)
    source_type = Column(String(30), nullable=False)
    base_url = Column(String(255), nullable=True)
    collection_policy = Column(String(255), nullable=False, default="ETHICAL_PUBLIC_PERMITTED")
    active = Column(Boolean, default=True, nullable=False)
