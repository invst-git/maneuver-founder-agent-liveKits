from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class LeadProfile:
    lead_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    name: str | None = None
    role: str | None = None
    company: str | None = None
    website: str | None = None
    email: str | None = None
    phone: str | None = None
    location: str | None = None

    industry: str | None = None
    company_size: str | None = None
    problem: str | None = None
    current_workflow: str | None = None
    current_tools: str | None = None
    desired_solution: str | None = None
    timeline: str | None = None
    budget: str | None = None
    decision_maker: str | None = None
    success_metric: str | None = None
    next_step: str | None = None

    qualification: str = "unknown"
    notes: list[str] = field(default_factory=list)
    transcript: list[dict[str, Any]] = field(default_factory=list)

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if value is None:
                continue

            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue

            if hasattr(self, key):
                setattr(self, key, value)

        self.updated_at = utc_now_iso()
        self.qualification = self.compute_qualification()

    def add_note(self, note: str) -> None:
        note = note.strip()
        if note:
            self.notes.append(note)
            self.updated_at = utc_now_iso()

    def add_transcript_item(self, role: str, text: str, interrupted: bool = False) -> None:
        text = text.strip()
        if not text:
            return

        self.transcript.append(
            {
                "timestamp": utc_now_iso(),
                "role": role,
                "text": text,
                "interrupted": interrupted,
            }
        )
        self.updated_at = utc_now_iso()

    def compute_qualification(self) -> str:
        strong_signals = 0

        if self.problem:
            strong_signals += 1
        if self.timeline and self.timeline.lower() not in {"unknown", "not sure", "no idea"}:
            strong_signals += 1
        if self.budget and self.budget.lower() not in {"unknown", "not sure", "no idea"}:
            strong_signals += 1
        if self.decision_maker and any(
            word in self.decision_maker.lower()
            for word in ["yes", "founder", "owner", "ceo", "director", "head", "manager"]
        ):
            strong_signals += 1
        if self.success_metric:
            strong_signals += 1

        if strong_signals >= 4:
            return "hot"
        if strong_signals >= 2:
            return "warm"
        return "low-fit"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)