from typing import Optional
from pydantic import BaseModel, ConfigDict

class SourceBase(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    base_url: Optional[str] = None
    collection_policy: str = "ETHICAL_PUBLIC_PERMITTED"
    active: bool = True

class SourceCreate(SourceBase):
    pass

class SourceResponse(SourceBase):
    model_config = ConfigDict(from_attributes=True)
