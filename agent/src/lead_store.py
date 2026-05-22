from pathlib import Path
from typing import Any
import json


class LeadStore:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.touch(exist_ok=True)

    def append_snapshot(self, lead: dict[str, Any], event: str) -> None:
        record = {
            "event": event,
            "lead": lead,
        }

        with self.file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")

    def print_snapshot(self, lead: dict[str, Any], event: str) -> None:
        print("\n========== MANEUVER LEAD SNAPSHOT ==========")
        print(f"Event: {event}")
        print(json.dumps(lead, indent=2, ensure_ascii=False))
        print("===========================================\n")

    def persist(self, lead: dict[str, Any], event: str) -> None:
        self.append_snapshot(lead, event)
        self.print_snapshot(lead, event)