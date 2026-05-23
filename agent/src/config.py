from dataclasses import dataclass
import os


DEFAULT_TTS_MODEL = "cartesia/sonic-3"
DEFAULT_TTS_VOICE = "228fca29-3a0a-435c-8728-5cb483251068"
DEFAULT_TTS_LANGUAGE = "en"
DEFAULT_TTS_SPEED = 0.98
DEFAULT_TTS_VOLUME = 1.0
DEFAULT_TTS_EMOTION = ""


@dataclass(frozen=True)
class Settings:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    agent_name: str
    leads_file: str
    transcript_debug_enabled: bool
    transcripts_file: str
    tts_model: str
    tts_voice: str
    tts_language: str
    tts_speed: float
    tts_volume: float
    tts_emotion: str


def get_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        return float(raw_value)
    except ValueError:
        return default


def get_tts_emotion_env() -> str:
    emotion = os.getenv("TTS_EMOTION", DEFAULT_TTS_EMOTION).strip()
    if not emotion:
        return DEFAULT_TTS_EMOTION

    if not all(character.isalpha() or character in {"_", "-"} for character in emotion):
        return DEFAULT_TTS_EMOTION

    return emotion


def get_settings() -> Settings:
    livekit_url = os.getenv("LIVEKIT_URL", "").strip()
    livekit_api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
    agent_name = os.getenv("AGENT_NAME", "maneuver-founder-agent").strip()
    leads_file = os.getenv("LEADS_FILE", "../data/leads.jsonl").strip()
    transcript_debug_enabled = os.getenv("ENABLE_TRANSCRIPT_DEBUG", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    transcripts_file = os.getenv("TRANSCRIPTS_FILE", "../data/transcripts.jsonl").strip()
    tts_model = os.getenv("TTS_MODEL", DEFAULT_TTS_MODEL).strip() or DEFAULT_TTS_MODEL
    tts_voice = os.getenv("TTS_VOICE", DEFAULT_TTS_VOICE).strip() or DEFAULT_TTS_VOICE
    tts_language = os.getenv("TTS_LANGUAGE", DEFAULT_TTS_LANGUAGE).strip() or DEFAULT_TTS_LANGUAGE
    tts_speed = get_float_env("TTS_SPEED", DEFAULT_TTS_SPEED)
    tts_volume = get_float_env("TTS_VOLUME", DEFAULT_TTS_VOLUME)
    tts_emotion = get_tts_emotion_env()

    missing = []
    if not livekit_url:
        missing.append("LIVEKIT_URL")
    if not livekit_api_key:
        missing.append("LIVEKIT_API_KEY")
    if not livekit_api_secret:
        missing.append("LIVEKIT_API_SECRET")

    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    return Settings(
        livekit_url=livekit_url,
        livekit_api_key=livekit_api_key,
        livekit_api_secret=livekit_api_secret,
        agent_name=agent_name,
        leads_file=leads_file,
        transcript_debug_enabled=transcript_debug_enabled,
        transcripts_file=transcripts_file,
        tts_model=tts_model,
        tts_voice=tts_voice,
        tts_language=tts_language,
        tts_speed=tts_speed,
        tts_volume=tts_volume,
        tts_emotion=tts_emotion,
    )
