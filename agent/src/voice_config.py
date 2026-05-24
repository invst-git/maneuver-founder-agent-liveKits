from typing import Any

from livekit.agents import TurnHandlingOptions, inference

from src.config import Settings
from src.speech_text import normalize_spoken_text_stream


def build_tts_extra_kwargs(settings: Settings) -> dict[str, Any]:
    extra_kwargs: dict[str, Any] = {
        "speed": settings.tts_speed,
        "volume": settings.tts_volume,
        "add_timestamps": False,
    }

    if settings.tts_emotion:
        extra_kwargs["emotion"] = settings.tts_emotion

    return extra_kwargs


def build_tts(settings: Settings) -> inference.TTS:
    return inference.TTS(
        model=settings.tts_model,
        voice=settings.tts_voice,
        language=settings.tts_language,
        api_key=settings.livekit_api_key,
        api_secret=settings.livekit_api_secret,
        extra_kwargs=build_tts_extra_kwargs(settings),
    )


def build_turn_handling(turn_detection: Any | None = None) -> TurnHandlingOptions:
    options = TurnHandlingOptions(
        endpointing={
            "mode": "fixed",
            "min_delay": 0.8,
            "max_delay": 3.0,
        },
        interruption={
            "enabled": True,
            "min_duration": 0.35,
            "min_words": 1,
            "resume_false_interruption": False,
            "false_interruption_timeout": 0.8,
        },
        preemptive_generation={
            "enabled": True,
            "preemptive_tts": True,
        },
    )

    if turn_detection is not None:
        options["turn_detection"] = turn_detection

    return options


def build_tts_text_transforms():
    return [
        "filter_markdown",
        "filter_emoji",
        normalize_spoken_text_stream,
    ]
