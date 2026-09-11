from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.camera import Camera
from app.models.event import Event
from app.schemas.event import EventCreate, EventResponse


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


@router.post("/", response_model=EventResponse)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db)
):
    camera = db.query(Camera).filter(
        Camera.id == event_data.camera_id
    ).first()

    if not camera:
        raise HTTPException(
            status_code=404,
            detail="Camera not found"
        )

    event = Event(
        camera_id=event_data.camera_id,
        user_id=event_data.user_id,
        event_type=event_data.event_type,
        severity=event_data.severity,
        description=event_data.description,
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return event


@router.get("/", response_model=list[EventResponse])
def get_events(
    db: Session = Depends(get_db)
):
    return db.query(Event).order_by(
        Event.created_at.desc()
    ).all()


@router.patch("/{event_id}/resolve")
def resolve_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    event.status = "resolved"

    db.commit()

    return {
        "message": "Event resolved successfully",
        "event_id": event.id
    }
