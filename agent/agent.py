from __future__ import annotations

from dotenv import load_dotenv

from livekit import agents
from livekit.agents import (
    Agent,
    AgentSession,
    AgentServer,
    ConversationItemAddedEvent,
    RunContext,
    TurnHandlingOptions,
    function_tool,
)
from livekit.agents.llm import ChatMessage
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

from src.config import get_settings
from src.lead_capture import LeadProfile
from src.lead_store import LeadStore
from src.prompts import FOUNDER_AGENT_PROMPT, OPENING_GREETING


load_dotenv(".env.local")

settings = get_settings()
server = AgentServer()


class ManeuverFounderAgent(Agent):
    def __init__(self, lead: LeadProfile, store: LeadStore):
        self.lead = lead
        self.store = store

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

        self.lead.update(
            name=name,
            role=role,
            company=company,
            website=website,
            email=email,
            phone=phone,
            location=location,
            industry=industry,
            company_size=company_size,
            problem=problem,
            current_workflow=current_workflow,
            current_tools=current_tools,
            desired_solution=desired_solution,
            timeline=timeline,
            budget=budget,
            decision_maker=decision_maker,
            success_metric=success_metric,
            next_step=next_step,
        )

        if note:
            self.lead.add_note(note)

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
    async def save_lead(
        self,
        context: RunContext,
        reason: str = "manual_or_end_of_call_save",
    ) -> dict:
        """Persist the current lead profile.

        Use this when the user says they are done, wants to end the call,
        asks to save the details, asks to send the details, or asks for a summary.
        """

        context.disallow_interruptions()

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


@server.rtc_session(agent_name=settings.agent_name)
async def maneuver_agent(ctx: agents.JobContext):
    lead = LeadProfile()
    store = LeadStore(
        settings.leads_file,
        transcript_file_path=settings.transcripts_file,
        transcript_debug_enabled=settings.transcript_debug_enabled,
    )

    async def save_on_shutdown():
        if lead.is_persistable():
            store.upsert_lead(lead.to_lead_record(), event="session_shutdown")

    ctx.add_shutdown_callback(save_on_shutdown)

    session = AgentSession(
        stt="deepgram/nova-3:multi",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3:9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
        vad=silero.VAD.load(),
        turn_handling=TurnHandlingOptions(
            turn_detection=MultilingualModel(),
        ),
        use_tts_aligned_transcript=True,
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

    await session.start(
        room=ctx.room,
        agent=ManeuverFounderAgent(lead=lead, store=store),
    )

    await session.generate_reply(
        instructions=OPENING_GREETING,
    )


if __name__ == "__main__":
    agents.cli.run_app(server)
