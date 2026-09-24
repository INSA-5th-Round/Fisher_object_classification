"""Unified event model + Event Classification + logging (JSONL + CSV)."""
import json
import csv
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any


class EventType(str, Enum):
    INTRUSION = "intrusion"
    RESTRICTED_AREA = "restricted_area"
    LOITERING = "loitering"
    CROWD_THRESHOLD = "crowd_threshold"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class Event:
    event_type: EventType
    severity: Severity
    zone: str
    object_id: int
    timestamp: float
    message: str

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = asdict(self)
        d["timestamp_readable"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.timestamp))
        return d


class EventClassifier:
    """Central place all modules report to. Assigns severity and persists a running log."""

    SEVERITY_MAP = {
        EventType.INTRUSION: Severity.HIGH,
        EventType.RESTRICTED_AREA: Severity.HIGH,
        EventType.LOITERING: Severity.MEDIUM,
        EventType.CROWD_THRESHOLD: Severity.MEDIUM,
    }

    def __init__(self, log_path: str = "events_log.jsonl") -> None:
        self.log_path = log_path
        self.events: list[Event] = []
        # truncate previous run's log
        open(self.log_path, "w").close()

    def classify(
        self,
        event_type: EventType,
        zone: str,
        object_id: int,
        message: str,
    ) -> Event:
        severity = self.SEVERITY_MAP.get(event_type, Severity.LOW)
        event = Event(event_type, severity, zone, object_id, time.time(), message)
        self.events.append(event)
        self._persist(event)
        print(f"[{severity.value.upper()}] {event_type.value} :: {message}")
        return event

    def _persist(self, event: Event) -> None:
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def export_csv(self, csv_path: str = "events_log.csv") -> None:
        if not self.events:
            return
        with open(csv_path, "w", newline="") as f:
            fieldnames = list(self.events[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for e in self.events:
                writer.writerow(e.to_dict())
