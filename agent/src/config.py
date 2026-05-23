from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    agent_name: str
    leads_file: str
    transcript_debug_enabled: bool
    transcripts_file: str


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
    )
