"""Detection logic: Intrusion Detection, Restricted Area Monitor,
Loitering Detection, Crowd Counting.

Each module reads the current frame's tracked_objects dict ({id: (x, y)})
and reports through the shared EventClassifier.
"""
import time
from collections.abc import Iterable
from typing import Any, Protocol, TypeAlias
from events import EventType


Point: TypeAlias = tuple[float, float]
TrackedObjects: TypeAlias = dict[int, Point]
AlertKey: TypeAlias = tuple[str, int]


class Zone(Protocol):
    name: str
    zone_type: str

    def contains(self, point: Point) -> bool: ...


class Classifier(Protocol):
    def classify(self, event_type: EventType, zone_name: str, object_id: int,
                 message: str) -> Any: ...


Zones: TypeAlias = Iterable[Zone]


class IntrusionDetector:
    """Fires once when an object FIRST enters a 'watch'/'intrusion' zone (edge-triggered)."""

    def __init__(self, zones: Zones, classifier: Classifier, cooldown: float = 5):
        self.zones = [z for z in zones if z.zone_type in ("watch", "intrusion")]
        self.classifier = classifier
        self.cooldown = cooldown
        self._last_alert: dict[AlertKey, float] = {}
        self._inside_last_frame: set[AlertKey] = set()

    def update(self, tracked_objects: TrackedObjects) -> None:
        currently_inside: set[AlertKey] = set()
        for oid, centroid in tracked_objects.items():
            for zone in self.zones:
                key = (zone.name, oid)
                if zone.contains(centroid):
                    currently_inside.add(key)
                    if key not in self._inside_last_frame:
                        self._maybe_alert(zone.name, oid)
        self._inside_last_frame = currently_inside

    def _maybe_alert(self, zone_name: str, oid: int) -> None:
        key = (zone_name, oid)
        now = time.time()
        if now - self._last_alert.get(key, 0) < self.cooldown:
            return
        self._last_alert[key] = now
        self.classifier.classify(
            EventType.INTRUSION, zone_name, oid,
            f"Object {oid} entered monitored zone '{zone_name}'",
        )


class RestrictedAreaMonitor:
    """Continuously alerts (rate-limited) while an object remains inside a restricted zone."""

    def __init__(self, zones: Zones, classifier: Classifier, cooldown: float = 10):
        self.zones = [z for z in zones if z.zone_type == "restricted"]
        self.classifier = classifier
        self.cooldown = cooldown
        self._last_alert: dict[AlertKey, float] = {}

    def update(self, tracked_objects: TrackedObjects) -> None:
        now = time.time()
        for oid, centroid in tracked_objects.items():
            for zone in self.zones:
                if zone.contains(centroid):
                    key = (zone.name, oid)
                    if now - self._last_alert.get(key, 0) >= self.cooldown:
                        self._last_alert[key] = now
                        self.classifier.classify(
                            EventType.RESTRICTED_AREA, zone.name, oid,
                            f"Object {oid} present in restricted area '{zone.name}'",
                        )


class LoiteringDetector:
    """Flags an object that has stayed inside a monitored zone beyond a time threshold."""

    def __init__(self, zones: Zones, classifier: Classifier, tracker: Any,
                 threshold_seconds: float = 15, cooldown: float = 20):
        self.zones = zones
        self.classifier = classifier
        self.tracker = tracker
        self.threshold_seconds = threshold_seconds
        self.cooldown = cooldown
        self._zone_entry_time: dict[AlertKey, float] = {}
        self._last_alert: dict[AlertKey, float] = {}

    def update(self, tracked_objects: TrackedObjects) -> None:
        now = time.time()
        active_keys: set[AlertKey] = set()
        for oid, centroid in tracked_objects.items():
            for zone in self.zones:
                key = (zone.name, oid)
                if zone.contains(centroid):
                    active_keys.add(key)
                    if key not in self._zone_entry_time:
                        self._zone_entry_time[key] = now
                    dwell = now - self._zone_entry_time[key]
                    if dwell >= self.threshold_seconds and \
                       now - self._last_alert.get(key, 0) >= self.cooldown:
                        self._last_alert[key] = now
                        self.classifier.classify(
                            EventType.LOITERING, zone.name, oid,
                            f"Object {oid} has loitered in '{zone.name}' for {dwell:.0f}s",
                        )
        # Reset entry time for objects that left their zone
        for key in list(self._zone_entry_time.keys()):
            if key not in active_keys:
                del self._zone_entry_time[key]


class CrowdCounter:
    """Counts people (whole frame, or within one zone) and alerts above a threshold."""

    def __init__(self, classifier: Classifier, threshold: int = 10,
                 zone: Zone | None = None, cooldown: float = 10):
        self.classifier = classifier
        self.threshold = threshold
        self.zone = zone  # None = whole frame
        self.cooldown = cooldown
        self._last_alert = 0

    def count(self, tracked_objects: TrackedObjects) -> int:
        if self.zone is None:
            return len(tracked_objects)
        return sum(1 for c in tracked_objects.values() if self.zone.contains(c))

    def update(self, tracked_objects: TrackedObjects) -> int:
        current_count = self.count(tracked_objects)
        now = time.time()
        if current_count >= self.threshold and now - self._last_alert >= self.cooldown:
            self._last_alert = now
            zone_name = self.zone.name if self.zone else "full_frame"
            self.classifier.classify(
                EventType.CROWD_THRESHOLD, zone_name, -1,
                f"Crowd count reached {current_count} (threshold {self.threshold}) in '{zone_name}'",
            )
        return current_count
