from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraResponse


router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"]
)


@router.post("/", response_model=CameraResponse)
def create_camera(
    camera_data: CameraCreate,
    db: Session = Depends(get_db)
):
    camera = Camera(
        name=camera_data.name,
        camera_type=camera_data.camera_type,
        ip_address=camera_data.ip_address,
        stream_url=camera_data.stream_url,
        location=camera_data.location,
    )

    db.add(camera)
    db.commit()
    db.refresh(camera)

    return camera


@router.get("/", response_model=list[CameraResponse])
def get_cameras(
    db: Session = Depends(get_db)
):
    return db.query(Camera).all()


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    camera = db.query(Camera).filter(
        Camera.id == camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    return camera


@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db)
):
    camera = db.query(Camera).filter(
        Camera.id == camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    db.delete(camera)
    db.commit()

    return {
        "message": "Camera deleted successfully"
    }
