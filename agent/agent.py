from __future__ import annotations

import asyncio

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    AgentStateChangedEvent,
    ConversationItemAddedEvent,
    RunContext,
    function_tool,
)
from livekit.agents.llm import ChatMessage
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.config import get_settings
from src.call_control import EndCallManager, LiveKitRoomCloser
from src.email_followup import EmailFollowupService
from src.lead_capture import LeadProfile
from src.lead_store import LeadStore
from src.prompts import FOUNDER_AGENT_PROMPT, OPENING_GREETING
from src.ui_bridge import (
    MANEUVER_UI_INPUT_TOPIC,
    ManeuverUiBridge,
    clean_lead_field_updates,
    normalize_lead_field,
    parse_ui_input_event,
)
from src.voice_config import build_tts, build_tts_text_transforms, build_turn_handling


load_dotenv(".env.local")

settings = get_settings()
server = AgentServer()


class ManeuverFounderAgent(Agent):
    def __init__(
        self,
        lead: LeadProfile,
        store: LeadStore,
        ui_bridge: ManeuverUiBridge,
        end_call_manager: EndCallManager,
        email_followup: EmailFollowupService,
    ):
        self.lead = lead
        self.store = store
        self.ui_bridge = ui_bridge
        self.end_call_manager = end_call_manager
        self.email_followup = email_followup

        super().__init__(
            instructions=FOUNDER_AGENT_PROMPT,
        )

    @function_tool()
    async def capture_lead_info(
        self,
        context: RunContext,
        name: str | None = None,
        role: str | None = None,
        company: str | None = None,
        website: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        location: str | None = None,
        industry: str | None = None,
        company_size: str | None = None,
        problem: str | None = None,
        current_workflow: str | None = None,
        current_tools: str | None = None,
        desired_solution: str | None = None,
        timeline: str | None = None,
        budget: str | None = None,
        decision_maker: str | None = None,
        success_metric: str | None = None,
        next_step: str | None = None,
        note: str | None = None,
    ) -> dict:
        """Capture useful discovery-call information from the visitor.

        Use this whenever the visitor provides any detail about identity, company,
        problem, workflow, tools, timeline, budget, decision making, or next step.
        Do not use this for random small talk.
        """

        lead_fields = {
            "name": name,
            "role": role,
            "company": company,
            "website": website,
            "email": email,
            "phone": phone,
            "location": location,
            "industry": industry,
            "company_size": company_size,
            "problem": problem,
            "current_workflow": current_workflow,
            "current_tools": current_tools,
            "desired_solution": desired_solution,
            "timeline": timeline,
            "budget": budget,
            "decision_maker": decision_maker,
            "success_metric": success_metric,
            "next_step": next_step,
        }
        ui_updates = clean_lead_field_updates(lead_fields)
        previous_values = {
            field_name: getattr(self.lead, field_name, None) for field_name in ui_updates
        }

        self.lead.update(
            **lead_fields,
        )

        if note:
            self.lead.add_note(note)

        for field_name, value in ui_updates.items():
            already_reviewed = self.lead.field_statuses.get(field_name) in {
                "confirmed",
                "corrected",
            }
            if already_reviewed and previous_values.get(field_name) == value:
                continue

            self.lead.set_field_status(field_name, "pending")

        await self.ui_bridge.update_lead_fields(ui_updates)

        saved = False
        reason = "missing_contact_or_company_signal"

        if self.lead.is_persistable():
            self.store.upsert_lead(self.lead.to_lead_record(), event="capture_lead_info")
            saved = True
            reason = "lead_record_saved"

        return {
            "saved": saved,
            "lead_id": self.lead.lead_id,
            "qualification": self.lead.qualification,
            "reason": reason,
        }

    @function_tool()
    async def update_lead_field(
        self,
        context: RunContext,
        field: str,
        value: str,
    ) -> dict:
        """Capture one discovery field and update the frontend side panel.

        Prefer capture_lead_info when the visitor provides multiple useful details.
        """

        canonical_field = normalize_lead_field(field)
        if canonical_field is None:
            return {
                "saved": False,
                "sent": False,
                "reason": "invalid_field",
            }

        updates = clean_lead_field_updates({canonical_field: value})
        if not updates:
            return {
                "saved": False,
                "sent": False,
                "reason": "empty_value",
            }

        previous_value = getattr(self.lead, canonical_field, None)
        self.lead.update(**updates)
        already_reviewed = self.lead.field_statuses.get(canonical_field) in {
            "confirmed",
            "corrected",
        }
        if not already_reviewed or previous_value != updates[canonical_field]:
            self.lead.set_field_status(canonical_field, "pending")
        ui_result = await self.ui_bridge.update_lead_field(canonical_field, updates[canonical_field])

        saved = False
        reason = "missing_contact_or_company_signal"

        if self.lead.is_persistable():
            self.store.upsert_lead(self.lead.to_lead_record(), event="update_lead_field")
            saved = True
            reason = "lead_record_saved"

        return {
            "saved": saved,
            "sent": ui_result.get("sent", False),
            "lead_id": self.lead.lead_id,
            "qualification": self.lead.qualification,
            "reason": reason,
        }

    @function_tool()
    async def show_services_slide(self, context: RunContext) -> dict:
        """Show Maneuver's services on the frontend before answering service-list questions."""

        return await self.ui_bridge.show_services_slide()

    @function_tool()
    async def show_service_detail(self, context: RunContext, service_name: str) -> dict:
        """Zoom the frontend into a specific Maneuver service."""

        return await self.ui_bridge.show_service_detail(service_name)

    @function_tool()
    async def show_process_diagram(self, context: RunContext) -> dict:
        """Show Maneuver's process diagram on the frontend before answering process questions."""

        return await self.ui_bridge.show_process_diagram()

    @function_tool()
    async def show_workflow_diagram(self, context: RunContext) -> dict:
        """Show a workflow diagram on the frontend before answering workflow or diagram requests."""

        return await self.ui_bridge.show_workflow_diagram()

    @function_tool()
    async def show_default_view(self, context: RunContext) -> dict:
        """Reset the frontend visual panel to the default call view."""

        return await self.ui_bridge.show_default_view()

    @function_tool()
    async def save_lead(
        self,
        context: RunContext,
        reason: str = "manual_or_end_of_call_save",
    ) -> dict:
        """Persist the current lead profile.

        Use this when the user says they are done, wants to end the call,
        asks to save the details, asks to send the details, or asks for a summary.
        """

        if not self.lead.is_persistable():
            return {
                "saved": False,
                "lead_id": self.lead.lead_id,
                "qualification": self.lead.qualification,
                "reason": "missing_contact_or_company_signal",
                "message": "Lead profile needs a contact or company signal before it can be saved.",
            }

        self.lead.add_note(f"Lead saved. Reason: {reason}")
        self.store.upsert_lead(self.lead.to_lead_record(), event="save_lead")

        return {
            "saved": True,
            "lead_id": self.lead.lead_id,
            "qualification": self.lead.qualification,
            "message": "Lead profile saved successfully.",
        }

    @function_tool()
    async def end_call(
        self,
        context: RunContext,
        reason: str = "customer_requested_end_call",
    ) -> dict:
        """End the call after a short goodbye.

        Use this when the visitor clearly wants to leave, says goodbye, says
        they are done, asks to end the call, or says they have no more questions.
        """

        context.disallow_interruptions()

        saved = False
        if self.lead.is_persistable():
            self.lead.add_note(f"Call ended by customer intent. Reason: {reason}")
            self.store.upsert_lead(self.lead.to_lead_record(), event="end_call")
            saved = True

        email_result = await self.email_followup.send_followup(self.lead)
        end_state = self.end_call_manager.request_end_call(reason)

        return {
            **end_state,
            "saved": saved,
            "email": email_result,
            "lead_id": self.lead.lead_id,
            "qualification": self.lead.qualification,
        }

    async def apply_ui_input_event(self, event: dict) -> dict:
        action = event.get("action")
        payload = event.get("payload") or {}
        field = normalize_lead_field(str(payload.get("field", "")))
        value = payload.get("value")

        if field is None or not isinstance(value, str) or not value.strip():
            return {
                "applied": False,
                "reason": "invalid_payload",
            }

        status = "confirmed" if action == "confirm_lead_field" else "corrected"
        cleaned_value = value.strip()
        self.lead.update(**{field: cleaned_value})
        self.lead.set_field_status(field, status)
        ui_result = await self.ui_bridge.update_lead_field(field, cleaned_value, status=status)

        saved = False
        if self.lead.is_persistable():
            self.store.upsert_lead(self.lead.to_lead_record(), event=action)
            saved = True

        return {
            "applied": True,
            "saved": saved,
            "sent": ui_result.get("sent", False),
            "field": field,
            "status": status,
            "lead_id": self.lead.lead_id,
        }


@server.rtc_session(agent_name=settings.agent_name)
async def maneuver_agent(ctx: agents.JobContext):
    lead = LeadProfile()
    store = LeadStore(
        settings.leads_file,
        transcript_file_path=settings.transcripts_file,
        transcript_debug_enabled=settings.transcript_debug_enabled,
    )
    ui_bridge = ManeuverUiBridge(ctx.room)
    email_followup = EmailFollowupService(settings)
    end_call_manager = EndCallManager(
        LiveKitRoomCloser(
            settings=settings,
            room_name=ctx.job.room.name,
        )
    )

    async def save_on_shutdown():
        if lead.is_persistable():
            store.upsert_lead(lead.to_lead_record(), event="session_shutdown")

    ctx.add_shutdown_callback(save_on_shutdown)

    agent = ManeuverFounderAgent(
        lead=lead,
        store=store,
        ui_bridge=ui_bridge,
        end_call_manager=end_call_manager,
        email_followup=email_followup,
    )

    @ctx.room.on("data_received")
    def on_data_received(packet):
        if packet.topic != MANEUVER_UI_INPUT_TOPIC:
            return

        event = parse_ui_input_event(packet.data)
        if event is None:
            return

        asyncio.create_task(agent.apply_ui_input_event(event))

    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm="openai/gpt-4.1-mini",
        tts=build_tts(settings),
        vad=silero.VAD.load(),
        turn_handling=build_turn_handling(turn_detection=MultilingualModel()),
        use_tts_aligned_transcript=False,
        tts_text_transforms=build_tts_text_transforms(),
        aec_warmup_duration=0.5,
    )

    @session.on("conversation_item_added")
    def on_conversation_item_added(event: ConversationItemAddedEvent):
        if not isinstance(event.item, ChatMessage):
            return

        role = str(event.item.role)
        text = event.item.text_content or ""
        interrupted = bool(getattr(event.item, "interrupted", False))

        transcript_item = lead.add_transcript_item(
            role=role,
            text=text,
            interrupted=interrupted,
        )

        if transcript_item:
            store.append_transcript_event(lead.lead_id, transcript_item)

    @session.on("agent_state_changed")
    def on_agent_state_changed(event: AgentStateChangedEvent):
        end_call_manager.observe_agent_state(event.new_state)

    await session.start(
        room=ctx.room,
        agent=agent,
    )

    await session.generate_reply(
        instructions=OPENING_GREETING,
        allow_interruptions=True,
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
