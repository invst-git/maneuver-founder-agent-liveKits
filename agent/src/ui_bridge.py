from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any


MANEUVER_UI_TOPIC = "maneuver.ui"
MANEUVER_UI_INPUT_TOPIC = "maneuver.ui.input"

LEAD_UI_FIELDS = (
    "name",
    "role",
    "company",
    "website",
    "email",
    "phone",
    "location",
    "industry",
    "company_size",
    "problem",
    "current_workflow",
    "current_tools",
    "desired_solution",
    "timeline",
    "budget",
    "decision_maker",
    "success_metric",
    "next_step",
)

LEAD_FIELD_ALIASES = {
    "company size": "company_size",
    "decision maker status": "decision_maker",
    "decision maker": "decision_maker",
    "current workflow": "current_workflow",
    "current tools": "current_tools",
    "desired solution": "desired_solution",
    "success metric": "success_metric",
    "next step": "next_step",
}

LEAD_FIELD_STATUSES = {
    "pending",
    "confirmed",
    "corrected",
}

UI_INPUT_ACTIONS = {
    "confirm_lead_field",
    "correct_lead_field",
}

SERVICE_ALIASES = {
    "workflow": "intelligent_workflows",
    "workflows": "intelligent_workflows",
    "intelligent workflow": "intelligent_workflows",
    "intelligent workflows": "intelligent_workflows",
    "automation": "intelligent_workflows",
    "voice": "voice_ai",
    "voice ai": "voice_ai",
    "voice agent": "voice_ai",
    "voice agents": "voice_ai",
    "self learning ai agents": "self_learning_ai_agents",
    "self-learning ai agents": "self_learning_ai_agents",
    "ai agents": "self_learning_ai_agents",
    "agents": "self_learning_ai_agents",
    "bespoke applications": "bespoke_applications",
    "bespoke application": "bespoke_applications",
    "custom applications": "bespoke_applications",
    "custom apps": "bespoke_applications",
    "systems integration": "systems_integration",
    "system integration": "systems_integration",
    "integrations": "systems_integration",
    "integration": "systems_integration",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_lead_field(field: str) -> str | None:
    normalized = field.strip().lower().replace("-", " ").replace("_", " ")
    canonical = LEAD_FIELD_ALIASES.get(normalized, normalized.replace(" ", "_"))

    if canonical in LEAD_UI_FIELDS:
        return canonical

    return None


def normalize_service_name(service_name: str) -> str:
    normalized = " ".join(service_name.strip().lower().split())
    return SERVICE_ALIASES.get(normalized, normalized.replace(" ", "_"))


def clean_lead_field_updates(fields: dict[str, Any]) -> dict[str, str]:
    updates: dict[str, str] = {}

    for field, value in fields.items():
        canonical = normalize_lead_field(field)
        if canonical is None or value is None:
            continue

        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                updates[canonical] = cleaned
            continue

        updates[canonical] = str(value)

    return updates


def normalize_lead_field_status(status: Any, default: str = "pending") -> str:
    if not isinstance(status, str):
        return default

    normalized = status.strip().lower()
    if normalized in LEAD_FIELD_STATUSES:
        return normalized

    return default


def parse_ui_input_event(data: bytes | str) -> dict[str, Any] | None:
    try:
        raw = data.decode("utf-8") if isinstance(data, bytes) else data
        candidate = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
        return None

    if not isinstance(candidate, dict) or candidate.get("version") != 1:
        return None

    action = candidate.get("action")
    if action not in UI_INPUT_ACTIONS:
        return None

    payload = candidate.get("payload")
    if not isinstance(payload, dict):
        return None

    field = normalize_lead_field(str(payload.get("field", "")))
    if field is None:
        return None

    value = payload.get("value")
    if not isinstance(value, str) or not value.strip():
        return None

    return {
        "version": 1,
        "id": str(candidate.get("id") or uuid.uuid4()),
        "action": action,
        "payload": {
            "field": field,
            "value": value.strip(),
        },
    }


def make_ui_event(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "version": 1,
        "id": str(uuid.uuid4()),
        "action": action,
        "payload": payload or {},
        "created_at": utc_now_iso(),
    }


class ManeuverUiBridge:
    def __init__(self, room_or_participant: Any | None, topic: str = MANEUVER_UI_TOPIC):
        self.room_or_participant = room_or_participant
        self.topic = topic

    def _get_local_participant(self) -> Any | None:
        if self.room_or_participant is None:
            return None

        if hasattr(self.room_or_participant, "publish_data"):
            return self.room_or_participant

        try:
            return self.room_or_participant.local_participant
        except Exception:
            return None

    async def emit(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        event = make_ui_event(action, payload)
        local_participant = self._get_local_participant()

        if local_participant is None:
            return {
                "sent": False,
                "action": action,
                "event_id": event["id"],
                "reason": "missing_local_participant",
            }

        try:
            await local_participant.publish_data(
                json.dumps(event, separators=(",", ":")),
                reliable=True,
                topic=self.topic,
            )
        except Exception as exc:
            print(f"Maneuver UI event failed: action={action} error={exc}")
            return {
                "sent": False,
                "action": action,
                "event_id": event["id"],
                "reason": "publish_failed",
            }

        return {
            "sent": True,
            "action": action,
            "event_id": event["id"],
        }

    async def show_services_slide(self) -> dict[str, Any]:
        return await self.emit("show_services_slide")

    async def show_service_detail(self, service_name: str) -> dict[str, Any]:
        return await self.emit(
            "show_service_detail",
            {
                "service_name": service_name.strip(),
                "service_id": normalize_service_name(service_name),
            },
        )

    async def show_process_diagram(self) -> dict[str, Any]:
        return await self.emit("show_process_diagram")

    async def show_workflow_diagram(self) -> dict[str, Any]:
        return await self.emit("show_workflow_diagram")

    async def show_default_view(self) -> dict[str, Any]:
        return await self.emit("show_default_view")

    async def update_lead_field(
        self,
        field: str,
        value: str,
        status: str = "pending",
    ) -> dict[str, Any]:
        updates = clean_lead_field_updates({field: value})
        if not updates:
            return {
                "sent": False,
                "action": "update_lead_field",
                "reason": "invalid_or_empty_field",
            }

        canonical, cleaned_value = next(iter(updates.items()))
        return await self.emit(
            "update_lead_field",
            {
                "field": canonical,
                "value": cleaned_value,
                "status": normalize_lead_field_status(status),
            },
        )

    async def update_lead_fields(self, fields: dict[str, Any]) -> list[dict[str, Any]]:
        updates = clean_lead_field_updates(fields)
        results = []

        for field, value in updates.items():
            results.append(await self.update_lead_field(field, value))

        return results
