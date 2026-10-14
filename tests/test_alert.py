from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime
from alerts import AlertManager
from alerts.models import AlertEvent

manager = AlertManager(cooldown_seconds=10)

event = AlertEvent(
    event_type="Intrusion Detected",
    camera="Camera 01",
    confidence=0.94,
    timestamp=datetime.now().isoformat(timespec="seconds"),
    severity="HIGH",
    screenshot_path=None,
    message="Test event generated without the main backend."
)

print("First alert:")
print(manager.send_alert(event))

print("\nImmediate duplicate:")
print(manager.send_alert(event))
