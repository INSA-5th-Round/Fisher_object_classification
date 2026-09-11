from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.alert import Alert
from app.models.camera import Camera
from app.models.event import Event
from app.schemas.alert import AlertCreate, AlertResponse


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.post("/", response_model=AlertResponse)
def create_alert(
    alert_data: AlertCreate,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == alert_data.event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    camera = db.query(Camera).filter(
        Camera.id == alert_data.camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    alert = Alert(
        event_id=alert_data.event_id,
        camera_id=alert_data.camera_id,
        user_id=alert_data.user_id,
        alert_type=alert_data.alert_type,
        message=alert_data.message,
        status="pending",
    )

    db.add(alert)
    db.commit()
    db.refresh(alert)

    return alert


@router.get("/", response_model=list[AlertResponse])
def get_alerts(
    db: Session = Depends(get_db)
):
    return db.query(Alert).order_by(
        Alert.created_at.desc()
    ).all()


@router.patch("/{alert_id}/sent")
def mark_alert_sent(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.status = "sent"
    alert.sent_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Alert marked as sent"
    }
