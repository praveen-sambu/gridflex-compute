# ElevenLabs + Nemotron Voice-Memory Bounty

## Goal

This isolated GridFlex feature adds a long-running voice-memory agent for the bounty track. The agent keeps a session log, can answer questions about earlier events in the session, and can return ElevenLabs-generated audio from backend-only credentials.

The existing GridFlex demo remains separate:

- `/dashboard`
- `/dashboard/live-carbon`
- `/dashboard/control-loop`
- `/api/v1/demo`
- `/api/v1/live-carbon`
- `/api/v1/control-loop-demo`
- `/api/v1/gpu-pulse-demo`

## Architecture

- Backend module: `apps/api/app/voice_agent.py`
- Backend routes: `apps/api/app/main.py`
- UI page: `apps/ui/src/app/dashboard/voice-agent/page.tsx`
- UI component: `apps/ui/src/components/VoiceAgentDashboard.tsx`
- Export script: `scripts/export_voice_agent_logs.py`

The backend owns:

- persistent session logging to `data/runtime/voice_agent_session.jsonl`
- recent memory assembly for model prompts
- NVIDIA Nemotron requests through the OpenAI-compatible API
- ElevenLabs text-to-speech generation
- safe audio file serving from `data/runtime/voice_agent_audio/`

The UI owns:

- session timer and evidence display
- event log table
- chat input
- browser microphone capture via `SpeechRecognition` or `webkitSpeechRecognition` when available
- playback of ElevenLabs audio returned by backend routes

## Required Server-Side Env Vars

Set these on the backend host or in a local untracked environment file. Do not commit them.

- `NVIDIA_API_KEY`
- `NIM_BASE_URL`
- `NIM_MODEL`
- `NIM_TIMEOUT_SECONDS`
- `ELEVENLABS_API_KEY`
- `ELEVENLABS_VOICE_ID`
- `VOICE_AGENT_SESSION_ID`

## How To Run For 1h11m

1. Start the GridFlex API with the voice-agent routes available.
2. Open `/dashboard/voice-agent` and keep the session alive.
3. Log notable events during the demo with the event button or the event route.
4. Periodically ask the agent what happened earlier in the session.
5. Keep the backend process and this page running for at least 71 minutes.
6. Use the evidence endpoint to confirm uptime.

## Judge Flow

Suggested live checks for judges:

- ask the agent what happened earlier in the session
- ask about a specific logged demo event
- inspect the event log table on the voice-agent page
- inspect `/api/v1/voice-agent/evidence`
- export the session artifacts after the run

## Logging Demo Events

Example route:

```bash
curl -X POST http://scan-12.local:8000/api/v1/voice-agent/event \
  -H "Content-Type: application/json" \
  -d '{"event_type":"demo_event","message":"Manual GPU pulse was triggered."}'
```

Example memory question:

```bash
curl -X POST http://scan-12.local:8000/api/v1/voice-agent/message \
  -H "Content-Type: application/json" \
  -d '{"message":"What happened earlier in this session?"}'
```

## Export Logs

```bash
c:/VS Workspaces/Ganicore-Team-Hackathon/.venv/Scripts/python.exe scripts/export_voice_agent_logs.py
```

Default export target:

- `artifacts/voice-agent-session-export/`

Export contents:

- `voice_agent_session.jsonl`
- generated ElevenLabs audio files, if present
- `audio_manifest.json`

## Fallback Behavior

- If `NVIDIA_API_KEY` is unavailable, the backend falls back to log-aware text replies.
- If ElevenLabs is unavailable, the backend still returns text and session memory, but no audio URL.
- Browser microphone capture is optional and depends on browser support.

## Security Notes

- Secrets stay backend-only.
- ElevenLabs and NVIDIA keys are never exposed to the frontend.
- Audio serving is restricted to files inside the voice-agent audio directory.
- No secrets are committed as part of this feature.