from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


BUSINESS_CONTEXT_FIELDS = (
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

DISCOVERY_QUESTIONS = {
    "name": "By the way, what should I call you?",
    "company": "What company or team is this for?",
    "role": "What is your role there?",
    "problem": "What is the main workflow or problem you want fixed?",
    "current_workflow": "How does that workflow run today?",
    "current_tools": "What tools are involved in that process right now?",
    "desired_solution": "What would a good solution ideally do for you?",
    "timeline": "When would you ideally want something live?",
    "budget": "Do you already have a budget range in mind for solving this?",
    "decision_maker": "Who else would need to be involved in deciding on this?",
    "success_metric": "What would make this a clear win for you?",
    "email": "What email should I send the follow-up to?",
    "phone": "Is there a phone number we should keep on file for follow-up?",
    "next_step": "What would be the most useful next step after this call?",
    "company_size": "Roughly how large is the team or company?",
    "industry": "What industry are you in?",
    "website": "What is the company website?",
    "location": "Where are you based?",
}

DISCOVERY_REASONS = {
    "name": "identify the person on the call",
    "company": "connect the problem to a business context",
    "role": "understand the visitor's responsibility and authority",
    "problem": "understand the core pain before proposing anything",
    "current_workflow": "map how the work happens today",
    "current_tools": "understand integration and migration constraints",
    "desired_solution": "learn the outcome the visitor wants",
    "timeline": "qualify urgency and implementation planning",
    "budget": "qualify commercial fit",
    "decision_maker": "understand the buying process",
    "success_metric": "define what success should be measured against",
    "email": "enable the promised follow-up",
    "phone": "keep a backup follow-up channel",
    "next_step": "agree on a concrete action after the call",
    "company_size": "size the operational context",
    "industry": "understand domain constraints",
    "website": "help identify the business accurately",
    "location": "understand timezone and regional context",
}

DISCOVERY_PRIORITY_FIELDS = (
    "name",
    "company",
    "role",
    "problem",
    "current_workflow",
    "current_tools",
    "desired_solution",
    "timeline",
    "budget",
    "decision_maker",
    "success_metric",
    "email",
    "phone",
    "next_step",
    "company_size",
    "industry",
    "website",
    "location",
)

REQUIRED_DISCOVERY_FIELDS = (
    "name",
    "company",
    "problem",
    "timeline",
)

CONTACT_FIELDS = (
    "email",
    "phone",
)


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
    field_statuses: dict[str, str] = field(default_factory=dict)
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

    def set_field_status(self, field_name: str, status: str) -> None:
        if hasattr(self, field_name):
            self.field_statuses[field_name] = status
            self.updated_at = utc_now_iso()

    def add_transcript_item(
        self,
        role: str,
        text: str,
        interrupted: bool = False,
    ) -> dict[str, Any] | None:
        text = text.strip()
        if not text:
            return None

        item = {
            "timestamp": utc_now_iso(),
            "role": role,
            "text": text,
            "interrupted": interrupted,
        }

        self.transcript.append(item)
        self.updated_at = utc_now_iso()

        return item

    def has_business_context(self) -> bool:
        return any(bool(getattr(self, field_name)) for field_name in BUSINESS_CONTEXT_FIELDS)

    def has_contact_method(self) -> bool:
        return any(bool(getattr(self, field_name)) for field_name in CONTACT_FIELDS)

    def has_minimum_discovery(self) -> bool:
        return all(bool(getattr(self, field_name)) for field_name in REQUIRED_DISCOVERY_FIELDS) and self.has_contact_method()

    def next_missing_discovery_field(self, for_wrap_up: bool = False) -> dict[str, Any] | None:
        if for_wrap_up and not self.has_contact_method():
            return self.discovery_question_for_field("email")

        for field_name in DISCOVERY_PRIORITY_FIELDS:
            if not getattr(self, field_name):
                return self.discovery_question_for_field(field_name)

        return None

    def discovery_question_for_field(self, field_name: str) -> dict[str, Any]:
        contact_required = field_name in CONTACT_FIELDS and not self.has_contact_method()
        required_before_wrap_up = field_name in REQUIRED_DISCOVERY_FIELDS or contact_required

        return {
            "field": field_name,
            "question": DISCOVERY_QUESTIONS[field_name],
            "reason": DISCOVERY_REASONS[field_name],
            "required_before_wrap_up": required_before_wrap_up,
        }

    def is_persistable(self) -> bool:
        if self.email or self.phone or self.company or self.website:
            return True

        return bool(self.name and self.has_business_context())

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

    def to_lead_record(self) -> dict[str, Any]:
        record = asdict(self)
        record.pop("transcript", None)
        return record
