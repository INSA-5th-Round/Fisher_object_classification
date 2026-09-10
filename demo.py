from datetime import datetime
from alerts import AlertManager
from alerts.models import AlertEvent

def main():
    manager = AlertManager()

    event = AlertEvent(
        event_type="Restricted Area Intrusion",
        camera="Camera 01",
        confidence=0.96,
        timestamp=datetime.now().isoformat(timespec="seconds"),
        severity="CRITICAL",
        screenshot_path=None,
        message="Standalone FISHER Alert Layer demo."
    )

    result = manager.send_alert(event)
    print(result)

if __name__ == "__main__":
    main()
