from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class AlertEvent:
    event_type: str
    camera: str
    confidence: float
    timestamp: str
    severity: str = "HIGH"
    screenshot_path: Optional[str] = None
    message: Optional[str] = None

    def to_dict(self):
        return asdict(self)
