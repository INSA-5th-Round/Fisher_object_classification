from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    event_id: int
    camera_id: int
    user_id: int | None = None
    alert_type: str
    message: str


class AlertResponse(BaseModel):
    id: int
    event_id: int
    camera_id: int
    user_id: int | None
    alert_type: str
    message: str
    status: str
    sent_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
