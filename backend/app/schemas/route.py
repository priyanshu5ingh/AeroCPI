from pydantic import BaseModel, field_validator, ConfigDict

class RouteBase(BaseModel):
    route_id: str
    origin_code: str
    destination_code: str
    directionality: str = "OUTBOUND"
    active: bool = True

    @field_validator("destination_code")
    @classmethod
    def validate_origin_dest_different(cls, v: str, info) -> str:
        origin = info.data.get("origin_code")
        if origin and origin.upper() == v.upper():
            raise ValueError("Origin and destination airport codes cannot be the same")
        return v.upper()

    @field_validator("origin_code")
    @classmethod
    def uppercase_origin(cls, v: str) -> str:
        return v.upper()

class RouteCreate(RouteBase):
    pass

class RouteResponse(RouteBase):
    model_config = ConfigDict(from_attributes=True)
