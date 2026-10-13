from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.camera import Camera
from app.models.detection import Detection
from app.schemas.detection import (
    DetectionCreate,
    DetectionResponse,
)


router = APIRouter(
    prefix="/detections",
    tags=["Detections"]
)


@router.post("/", response_model=DetectionResponse)
def create_detection(
    detection_data: DetectionCreate,
    db: Session = Depends(get_db)
):
    camera = db.query(Camera).filter(
        Camera.id == detection_data.camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    detection = Detection(
        camera_id=detection_data.camera_id,
        object_type=detection_data.object_type,
        confidence=detection_data.confidence,
        tracking_id=detection_data.tracking_id,
        bounding_box=detection_data.bounding_box,
    )

    db.add(detection)
    db.commit()
    db.refresh(detection)

    return detection


@router.get("/", response_model=list[DetectionResponse])
def get_detections(
    db: Session = Depends(get_db)
):
    return db.query(Detection).order_by(
        Detection.detected_at.desc()
    ).all()


@router.get(
    "/camera/{camera_id}",
    response_model=list[DetectionResponse]
)
def get_camera_detections(
    camera_id: int,
    db: Session = Depends(get_db)
):
    return db.query(Detection).filter(
        Detection.camera_id == camera_id
    ).order_by(
        Detection.detected_at.desc()
    ).all()
