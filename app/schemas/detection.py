from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DetectionCreate(BaseModel):
    camera_id: int
    object_type: str
    confidence: float
    tracking_id: int | None = None
    bounding_box: dict | None = None


class DetectionResponse(BaseModel):
    id: int
    camera_id: int
    object_type: str
    confidence: float
    tracking_id: int | None
    bounding_box: dict | None
    detected_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )
