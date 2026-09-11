from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventCreate(BaseModel):
    camera_id: int
    user_id: int | None = None
    event_type: str
    severity: str = "medium"
    description: str | None = None


class EventResponse(BaseModel):
    id: int
    camera_id: int
    user_id: int | None
    event_type: str
    severity: str
    description: str | None
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
