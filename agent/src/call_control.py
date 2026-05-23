from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Callable

from livekit import api

from src.config import Settings


END_CALL_INTENT_EXAMPLES = (
    "bye",
    "goodbye",
    "that is all",
    "that's all",
    "that'll be all",
    "talk later",
    "end the call",
    "end call",
    "hang up",
    "disconnect",
    "i am done",
    "i'm done",
    "we are done",
    "we're done",
    "no more questions",
    "nothing else",
    "thanks, bye",
    "thank you, bye",
)


def is_end_call_intent(text: str) -> bool:
    normalized = " ".join(text.strip().lower().replace(".", " ").replace(",", " ").split())
    if not normalized:
        return False

    return any(example in normalized for example in END_CALL_INTENT_EXAMPLES)


class LiveKitRoomCloser:
    def __init__(
        self,
        settings: Settings,
        room_name: str,
        api_factory: Callable[..., Any] = api.LiveKitAPI,
    ):
        self.settings = settings
        self.room_name = room_name
        self.api_factory = api_factory

    async def delete_room(self) -> dict[str, Any]:
        if not self.room_name:
            return {
                "closed": False,
                "reason": "missing_room_name",
            }

        lkapi = self.api_factory(
            url=self.settings.livekit_url,
            api_key=self.settings.livekit_api_key,
            api_secret=self.settings.livekit_api_secret,
        )

        try:
            await lkapi.room.delete_room(api.DeleteRoomRequest(room=self.room_name))
        finally:
            await lkapi.aclose()

        return {
            "closed": True,
            "room": self.room_name,
        }


@dataclass
class EndCallState:
    requested: bool = False
    final_response_started: bool = False
    closing_started: bool = False
    closed: bool = False
    reason: str = ""
    trigger: str = ""


class EndCallManager:
    def __init__(
        self,
        closer: LiveKitRoomCloser,
        *,
        close_delay_seconds: float = 0.8,
        fallback_seconds: float = 10.0,
    ):
        self.closer = closer
        self.close_delay_seconds = close_delay_seconds
        self.fallback_seconds = fallback_seconds
        self.state = EndCallState()
        self.close_task: asyncio.Task | None = None
        self.fallback_task: asyncio.Task | None = None

    def request_end_call(self, reason: str) -> dict[str, Any]:
        cleaned_reason = reason.strip() or "customer_requested_end_call"
        self.state.requested = True
        self.state.reason = cleaned_reason
        self._schedule_fallback()

        return {
            "ending_call": True,
            "reason": cleaned_reason,
            "message": "Say a short warm goodbye now. The room will close after your goodbye finishes.",
        }

    def observe_agent_state(self, new_state: str) -> None:
        if not self.state.requested or self.state.closing_started:
            return

        if new_state == "speaking":
            self.state.final_response_started = True
            return

        if self.state.final_response_started and new_state in {"idle", "listening"}:
            self._schedule_close("agent_finished_goodbye")

    def _schedule_fallback(self) -> None:
        if self.fallback_task and not self.fallback_task.done():
            return

        self.fallback_task = asyncio.create_task(self._close_after_fallback())

    def _schedule_close(self, trigger: str) -> None:
        if self.close_task and not self.close_task.done():
            return

        self.close_task = asyncio.create_task(self._close_after_delay(trigger))

    async def _close_after_delay(self, trigger: str) -> None:
        if self.close_delay_seconds > 0:
            await asyncio.sleep(self.close_delay_seconds)

        await self.close_now(trigger)

    async def _close_after_fallback(self) -> None:
        if self.fallback_seconds > 0:
            await asyncio.sleep(self.fallback_seconds)

        await self.close_now("fallback_timeout")

    async def close_now(self, trigger: str) -> dict[str, Any]:
        if self.state.closing_started:
            return {
                "closed": self.state.closed,
                "reason": "close_already_started",
            }

        self.state.closing_started = True
        self.state.trigger = trigger

        try:
            result = await self.closer.delete_room()
            self.state.closed = bool(result.get("closed"))
            return result
        except Exception as exc:
            print(f"Maneuver end-call room close failed: trigger={trigger} error={exc}")
            return {
                "closed": False,
                "reason": "delete_room_failed",
            }
