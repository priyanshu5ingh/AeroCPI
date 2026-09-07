import uuid
from sqlalchemy import Column, String, Integer, Float, Date, ForeignKey
from app.db.base import Base

class RouteIndexResult(Base):
    __tablename__ = "route_index_results"

    result_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("index_runs.run_id"), nullable=False, index=True)
    route_id = Column(String(15), ForeignKey("routes.route_id"), nullable=False, index=True)
    origin_code = Column(String(10), nullable=False)
    destination_code = Column(String(10), nullable=False)
    travel_date = Column(Date, nullable=True)
    booking_horizon = Column(Integer, nullable=False)
    cabin = Column(String(20), nullable=False, default="ECONOMY")
    stop_type = Column(String(20), nullable=False, default="NON_STOP")
    
    reference_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    price_relative = Column(Float, nullable=False)
    route_index_value = Column(Float, nullable=False)
    weight_share = Column(Float, nullable=False)
    
    sample_count = Column(Integer, nullable=False, default=0)
    eligible_count = Column(Integer, nullable=False, default=0)
    excluded_count = Column(Integer, nullable=False, default=0)
    flagged_count = Column(Integer, nullable=False, default=0)
