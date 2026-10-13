"""Polygon zone utilities for restricted-area / intrusion / counting checks."""
import numpy as np
import cv2
from collections.abc import Mapping, Sequence
from typing import Any, cast


class Zone:
    def __init__(
        self,
        name: str,
        polygon: Sequence[Sequence[int]],
        zone_type: str = "restricted",
    ) -> None:
        self.name = name
        self.polygon = np.array(polygon, dtype=np.int32)
        self.zone_type = zone_type  # "restricted" | "watch" | "counting"

    def contains(self, point: tuple[float, float]) -> bool:
        result = cast(
            float,
            cv2.pointPolygonTest(self.polygon, point, False),  # type: ignore[reportUnknownMemberType]
        )
        return result >= 0

    def draw(
        self,
        frame: Any,
        color: tuple[int, int, int] = (0, 0, 255),
        thickness: int = 2,
    ) -> Any:
        cv2.polylines(  # type: ignore[reportUnknownMemberType]
            frame,
            [self.polygon],
            isClosed=True,
            color=color,
            thickness=thickness,
        )
        return frame


def load_zones(config: Mapping[str, Any]) -> list[Zone]:
    zones: list[Zone] = []
    raw_zones = cast(Sequence[Mapping[str, Any]], config.get("zones", []))
    for z in raw_zones:
        zones.append(Zone(z["name"], z["polygon"], z.get("type", "restricted")))
    return zones
