from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DatasetVersionBase(BaseModel):
    dataset_version_id: str
    description: str
    source_status: str = "OBSERVED"
    record_count: int = 0
    fingerprint: str

class DatasetVersionCreate(DatasetVersionBase):
    pass

class DatasetVersionResponse(DatasetVersionBase):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
