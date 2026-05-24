from dataclasses import dataclass
import os


DEFAULT_TTS_MODEL = "cartesia/sonic-3"
DEFAULT_TTS_VOICE = "228fca29-3a0a-435c-8728-5cb483251068"
DEFAULT_TTS_LANGUAGE = "en"
DEFAULT_TTS_SPEED = 0.98
DEFAULT_TTS_VOLUME = 1.0
DEFAULT_TTS_EMOTION = ""
DEFAULT_SMTP_PORT = 587


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
    followup_email_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = DEFAULT_SMTP_PORT
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    internal_lead_email: str = ""


def get_bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name, "").strip().lower()
    if not raw_value:
        return default

    return raw_value in {"1", "true", "yes", "on"}


def get_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


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
    followup_email_enabled = get_bool_env("FOLLOWUP_EMAIL_ENABLED", False)
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = get_int_env("SMTP_PORT", DEFAULT_SMTP_PORT)
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_use_tls = get_bool_env("SMTP_USE_TLS", True)
    email_from = os.getenv("EMAIL_FROM", "").strip()
    internal_lead_email = os.getenv("INTERNAL_LEAD_EMAIL", "").strip()

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
        followup_email_enabled=followup_email_enabled,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        email_from=email_from,
        internal_lead_email=internal_lead_email,
    )
