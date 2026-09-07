from typing import Optional
from pydantic import BaseModel, ConfigDict

class CarrierBase(BaseModel):
    carrier_id: str
    iata_code: Optional[str] = None
    display_name: str
    active: bool = True

class CarrierCreate(CarrierBase):
    pass

class CarrierResponse(CarrierBase):
    model_config = ConfigDict(from_attributes=True)
