from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from email.message import EmailMessage
import re
import smtplib
from typing import Callable

from src.config import Settings
from src.lead_capture import LeadProfile


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class FollowupEmailResult:
    enabled: bool
    customer_sent: bool = False
    internal_sent: bool = False
    duplicate_skipped: bool = False
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "customer_sent": self.customer_sent,
            "internal_sent": self.internal_sent,
            "duplicate_skipped": self.duplicate_skipped,
            "errors": list(self.errors),
        }


def is_valid_email(email: str | None) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def display_value(value: str | None) -> str:
    if value is None:
        return "Not captured"

    cleaned = value.strip()
    return cleaned or "Not captured"


def render_customer_followup_body(lead: LeadProfile) -> str:
    name = lead.name.strip() if lead.name else "there"
    lines = [
        f"Hi {name},",
        "",
        "Thanks for speaking with Maneuver. Here is the short recap from the call:",
        "",
        f"- Company: {display_value(lead.company)}",
        f"- Problem: {display_value(lead.problem)}",
        f"- Current workflow: {display_value(lead.current_workflow)}",
        f"- Desired solution: {display_value(lead.desired_solution)}",
        f"- Timeline: {display_value(lead.timeline)}",
        f"- Next step: {display_value(lead.next_step)}",
        "",
        "If this still looks right, the next step is a focused discovery follow-up so we can scope what is actually worth building.",
        "",
        "Maneuver",
    ]
    return "\n".join(lines)


def render_internal_lead_body(lead: LeadProfile) -> str:
    fields = [
        ("Lead ID", lead.lead_id),
        ("Qualification", lead.qualification),
        ("Name", lead.name),
        ("Role", lead.role),
        ("Company", lead.company),
        ("Website", lead.website),
        ("Email", lead.email),
        ("Phone", lead.phone),
        ("Location", lead.location),
        ("Industry", lead.industry),
        ("Company size", lead.company_size),
        ("Problem", lead.problem),
        ("Current workflow", lead.current_workflow),
        ("Current tools", lead.current_tools),
        ("Desired solution", lead.desired_solution),
        ("Timeline", lead.timeline),
        ("Budget", lead.budget),
        ("Decision maker", lead.decision_maker),
        ("Success metric", lead.success_metric),
        ("Next step", lead.next_step),
    ]

    lines = ["New Maneuver lead captured", ""]
    for label, value in fields:
        lines.append(f"{label}: {display_value(value)}")

    if lead.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in lead.notes)

    return "\n".join(lines)


def build_email_message(
    *,
    sender: str,
    recipient: str,
    subject: str,
    body: str,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    return message


class EmailFollowupService:
    def __init__(
        self,
        settings: Settings,
        smtp_factory: Callable[..., smtplib.SMTP] = smtplib.SMTP,
    ):
        self.settings = settings
        self.smtp_factory = smtp_factory
        self.attempted_lead_ids: set[str] = set()

    async def send_followup(self, lead: LeadProfile) -> dict:
        result = await asyncio.to_thread(self._send_followup_sync, lead)
        return result.to_dict()

    def _send_followup_sync(self, lead: LeadProfile) -> FollowupEmailResult:
        if lead.lead_id in self.attempted_lead_ids:
            return FollowupEmailResult(
                enabled=self.settings.followup_email_enabled,
                duplicate_skipped=True,
            )

        self.attempted_lead_ids.add(lead.lead_id)
        result = FollowupEmailResult(enabled=self.settings.followup_email_enabled)

        if not self.settings.followup_email_enabled:
            return result

        messages = self._build_messages(lead)
        if not messages:
            return result

        if not self.settings.smtp_host:
            result.errors.append("missing_smtp_host")
            return result

        if not self.settings.email_from:
            result.errors.append("missing_email_from")
            return result

        try:
            with self.smtp_factory(
                self.settings.smtp_host,
                self.settings.smtp_port,
                timeout=10,
            ) as smtp:
                if self.settings.smtp_use_tls:
                    smtp.starttls()

                if self.settings.smtp_username or self.settings.smtp_password:
                    smtp.login(self.settings.smtp_username, self.settings.smtp_password)

                for kind, message in messages:
                    smtp.send_message(message)
                    if kind == "customer":
                        result.customer_sent = True
                    if kind == "internal":
                        result.internal_sent = True
        except Exception as exc:
            result.errors.append(f"smtp_send_failed:{exc}")
            print(f"Maneuver follow-up email failed: lead_id={lead.lead_id} error={exc}")

        return result

    def _build_messages(self, lead: LeadProfile) -> list[tuple[str, EmailMessage]]:
        messages: list[tuple[str, EmailMessage]] = []
        sender = self.settings.email_from

        if is_valid_email(lead.email):
            messages.append(
                (
                    "customer",
                    build_email_message(
                        sender=sender,
                        recipient=lead.email.strip(),
                        subject="Your Maneuver follow-up",
                        body=render_customer_followup_body(lead),
                    ),
                )
            )

        if is_valid_email(self.settings.internal_lead_email) and lead.is_persistable():
            lead_name = lead.name or lead.company or "new lead"
            messages.append(
                (
                    "internal",
                    build_email_message(
                        sender=sender,
                        recipient=self.settings.internal_lead_email,
                        subject=f"New Maneuver lead: {lead_name}",
                        body=render_internal_lead_body(lead),
                    ),
                )
            )

        return messages
