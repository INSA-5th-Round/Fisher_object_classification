from typing import Optional, List
from pydantic import BaseModel, Field


class DetectionEvent(BaseModel):
    id: str
    cameraId: str = "CAM-001"
    type: str = "Person detected"
    confidence: float = Field(ge=0, le=100)
    severity: str = Field(default="high", description="Allowed: low | medium | high | critical")
    timestamp: str
    status: str = Field(default="new", description="Allowed: new | reviewed | dismissed")
    description: Optional[str] = ""
    image: Optional[str] = None
    video: Optional[str] = None
    imageUrl: Optional[str] = None
    videoUrl: Optional[str] = None


class DetectionStatusUpdate(BaseModel):
    status: Optional[str] = None
    video: Optional[str] = None
    videoUrl: Optional[str] = None
    image: Optional[str] = None
    imageUrl: Optional[str] = None
    video_ready: Optional[bool] = None


class VideoUpdateRequest(BaseModel):
    video: str
    videoUrl: Optional[str] = None
    video_ready: Optional[bool] = True


class AlertUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    image: Optional[str] = None
    imageUrl: Optional[str] = None
    video: Optional[str] = None
    videoUrl: Optional[str] = None


class CameraModel(BaseModel):
    id: str = "CAM-001"
    name: str = "PC Camera (OpenCV)"
    location: str = "Local Workstation"
    status: str = "online"
    streamUrl: Optional[str] = "/api/cameras/CAM-001/stream"


class AlertNotifyRequest(BaseModel):
    channels: List[str] = Field(default_factory=lambda: ["sms", "telegram"])
    alertId: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    cameraId: Optional[str] = None
    confidence: Optional[float] = None
    incidentUrl: Optional[str] = None


class TelegramTestRequest(BaseModel):
    message: Optional[str] = "🚨 FISHER CCTV Alert System: Test connection successful."


class LoginRequest(BaseModel):
    username: str
    email: str
    password: str


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str


class UserCreateRequest(BaseModel):
    name: str
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: str = "operator"


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    title: Optional[str] = "Detection Activity Report"
