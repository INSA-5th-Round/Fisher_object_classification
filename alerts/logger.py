import json
from pathlib import Path
from datetime import datetime

class AlertLogger:
    def __init__(self, log_path="logs/alerts.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, payload):
        record = {
            "logged_at": datetime.now().isoformat(timespec="seconds"),
            **payload
        }
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
