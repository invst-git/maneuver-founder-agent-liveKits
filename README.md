# Maneuver LiveKit Voice Agent

This repo runs a real-time founder-style discovery call for Maneuver. It has two parts:

- `agent/`: LiveKit voice agent that handles speech, discovery, visual UI tool calls, lead capture, call ending, and follow-up email.
- `web/`: Next.js frontend for joining the LiveKit room, showing the voice UI, rendering live visuals, and letting users confirm or correct captured lead fields.

Lead records are stored as compact JSONL records in `data/leads.jsonl`. Full transcripts are not stored in the lead record; transcript debug logging is opt-in.

## Run Locally

Prerequisites:

- Python 3.12+
- `uv`
- Node.js and `pnpm`
- A LiveKit Cloud project with `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`

Create env files:

```powershell
Copy-Item .\web\.env.example .\web\.env.local
Copy-Item .\web\.env.example .\agent\.env.local
```

Fill both `.env.local` files with at least:

```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
AGENT_NAME=maneuver-founder-agent
LEADS_FILE=../data/leads.jsonl
```

Optional follow-up email settings, only needed when `FOLLOWUP_EMAIL_ENABLED=true`.
The current implementation uses SMTP, and the tested provider is Twilio SendGrid:

```env
FOLLOWUP_EMAIL_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_USE_TLS=true
EMAIL_FROM=your_verified_sender@yourdomain.com
INTERNAL_LEAD_EMAIL=leads@yourdomain.com
```

Install dependencies:

```powershell
cd .\agent
uv sync

cd ..\web
pnpm install
```

Run in two PowerShell terminals:

```powershell
cd C:\Side-Projects\maneuver-livekit\agent
uv run python agent.py dev
```

```powershell
cd C:\Side-Projects\maneuver-livekit\web
pnpm dev
```

Open:

```text
http://localhost:3000
```

Useful checks:

```powershell
cd .\agent
uv run python -m unittest discover -s tests
```

```powershell
cd .\web
pnpm exec tsc --noEmit --pretty false
```

## Models And Providers

- **LiveKit Cloud / LiveKit Agents**: real-time room, audio transport, agent dispatch, data-channel UI events, and the Python voice-agent runtime. This keeps audio, interruptions, tool calls, and frontend sync in one realtime stack.
- **Deepgram `nova-3:multi` for STT**: used through LiveKit inference for low-latency multilingual speech recognition. Good fit for live calls where users may speak naturally or interrupt.
- **OpenAI `gpt-4.1-mini` for the LLM**: used for the conversation, discovery reasoning, and tool calling. Chosen for fast responses, lower cost, and strong enough instruction/tool-following for this workflow.
- **Cartesia `sonic-3` via LiveKit Inference for TTS**: used for realtime voice output. The app disables timestamp/aligned transcript overhead and tunes interruption handling to reduce robotic pauses.
- **Silero VAD**: local voice activity detection for when the user starts and stops speaking. It is lightweight and works well for realtime turn handling.
- **LiveKit multilingual turn detector**: improves end-of-turn detection beyond basic silence checks, which helps prevent the agent from jumping in too early or waiting too long.
- **Twilio SendGrid over SMTP for follow-up email**: the app sends real post-call follow-up emails through SendGrid's SMTP relay (`smtp.sendgrid.net`, username `apikey`, password as the SendGrid API key). This keeps the implementation simple and still lets the provider be swapped later because the app only depends on SMTP settings.
- **Local JSONL storage**: simple local persistence for leads while iterating. It stores compact lead data and confirmation status, not full lead snapshots or transcripts.

## What I Would Do Next With One More Week

1. **Harden production security**
   - Add authentication to `/api/token`.
   - Lock down any lead-read APIs with `LEADS_API_KEY` or real auth.
   - Rotate local secrets and move production secrets into the hosting provider's secret store.

2. **Move lead storage to a database**
   - Replace `data/leads.jsonl` with Postgres or Supabase.
   - Keep the same compact lead schema.
   - Add a small admin view for filtering captured leads and confirmation status.

3. **Improve voice QA**
   - Test 3-5 Cartesia voices with the same prompt and TTS settings.
   - Add a small scripted call checklist for interruption, silence, noisy mic, and fast back-and-forth cases.
   - Tune `min_duration`, `aec_warmup_duration`, and TTS speed based on those recordings.

4. **Make visual routing more reliable**
   - Add deterministic frontend fallback rules for services, process, workflow, pricing, and integrations.
   - Add tests for common user phrasings like "show me a diagram" and "how does this workflow work?"
   - Log missed visual intents during local testing.

5. **Operational polish**
   - Add structured logs for call start/end, lead saved, email sent/failed, and tool-call failures.
   - Add retry/backoff for follow-up email failures.
   - Add a simple health check for the agent and frontend env configuration.

6. **Deployment pass**
   - Deploy web and agent separately.
   - Confirm LiveKit agent dispatch works in the deployed environment.
   - Run one stress test after deployment and one real end-to-end discovery call.
