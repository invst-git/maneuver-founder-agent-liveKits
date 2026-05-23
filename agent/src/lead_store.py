from pathlib import Path
from typing import Any
import json


class LeadStore:
    def __init__(
        self,
        file_path: str,
        transcript_file_path: str | None = None,
        transcript_debug_enabled: bool = False,
    ):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file_path.touch(exist_ok=True)
        self.transcript_file_path = Path(transcript_file_path) if transcript_file_path else None
        self.transcript_debug_enabled = transcript_debug_enabled

    def _read_lead_records(self) -> list[dict[str, Any]]:
        records_by_id: dict[str, dict[str, Any]] = {}

        content = self.file_path.read_text(encoding="utf-8").strip()
        if not content:
            return []

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            record = self._compact_record(json.loads(line))
            if not record:
                continue

            lead_id = record.get("lead_id")
            if isinstance(lead_id, str) and lead_id:
                records_by_id[lead_id] = record

        return list(records_by_id.values())

    def _compact_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        source = record.get("lead") if isinstance(record.get("lead"), dict) else record
        lead_id = source.get("lead_id")

        if not isinstance(lead_id, str) or not lead_id:
            return None

        compact = dict(source)
        compact.pop("event", None)
        compact.pop("transcript", None)

        return compact

    def upsert_lead(self, lead: dict[str, Any], event: str) -> None:
        lead_id = lead.get("lead_id")
        if not isinstance(lead_id, str) or not lead_id:
            raise ValueError("Lead record must include a non-empty lead_id")

        records_by_id = {record["lead_id"]: record for record in self._read_lead_records()}
        records_by_id[lead_id] = self._compact_record(lead) or lead

        temp_path = self.file_path.with_suffix(f"{self.file_path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            for record in records_by_id.values():
                file.write(json.dumps(record, ensure_ascii=False) + "\n")

        temp_path.replace(self.file_path)

        qualification = lead.get("qualification", "unknown")
        print(f"Maneuver lead saved: lead_id={lead_id} qualification={qualification} event={event}")

    def append_transcript_event(self, lead_id: str, item: dict[str, Any]) -> None:
        if not self.transcript_debug_enabled or self.transcript_file_path is None:
            return

        self.transcript_file_path.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "lead_id": lead_id,
            **item,
        }

        with self.transcript_file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
