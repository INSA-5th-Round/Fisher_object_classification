from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CameraCreate(BaseModel):
    name: str
    camera_type: str = "IP"
    ip_address: str | None = None
    stream_url: str
    location: str | None = None


class CameraResponse(BaseModel):
    id: int
    name: str
    camera_type: str
    ip_address: str | None
    stream_url: str
    location: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
