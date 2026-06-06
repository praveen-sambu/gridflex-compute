from __future__ import annotations

import json
import os
import shutil
import threading
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = ROOT / "data" / "runtime"
SESSION_LOG_PATH = RUNTIME_DIR / "voice_agent_session.jsonl"
AUDIO_DIR = RUNTIME_DIR / "voice_agent_audio"
TARGET_MINUTES = 71
DEFAULT_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NIM_MODEL = "nvidia/nemotron-3-ultra-550b-a55b"
DEFAULT_NIM_TIMEOUT_SECONDS = 60.0
DEFAULT_SYSTEM_PROMPT = (
    "You are GridFlex Voice Agent, an operations assistant. "
    "You remember the current session log and answer questions about what happened earlier. "
    "Be concise and truthful. If something is not in the log, say you do not know."
)
DEFAULT_ELEVENLABS_MODEL = "eleven_multilingual_v2"
DEFAULT_ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
MAX_MEMORY_EVENTS = 100
MAX_MEMORY_CHARS = 7000
_WRITE_LOCK = threading.Lock()


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _runtime_path_ready() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def _session_id() -> str:
    value = os.getenv("VOICE_AGENT_SESSION_ID", "").strip()
    return value or "gridflex-bounty-session-001"


def _nvidia_api_key() -> str | None:
    value = os.getenv("NVIDIA_API_KEY", "").strip()
    return value or None


def _nim_base_url() -> str:
    value = os.getenv("NIM_BASE_URL", "").strip()
    return value.rstrip("/") if value else DEFAULT_NIM_BASE_URL


def _nim_model() -> str:
    value = os.getenv("NIM_MODEL", "").strip()
    return value or DEFAULT_NIM_MODEL


def _nim_timeout_seconds() -> float:
    raw = os.getenv("NIM_TIMEOUT_SECONDS", "").strip()
    try:
        timeout = float(raw) if raw else DEFAULT_NIM_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_NIM_TIMEOUT_SECONDS
    return timeout if timeout > 0 else DEFAULT_NIM_TIMEOUT_SECONDS


def _elevenlabs_api_key() -> str | None:
    value = os.getenv("ELEVENLABS_API_KEY", "").strip()
    return value or None


def _elevenlabs_voice_id() -> str | None:
    value = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
    return value or DEFAULT_ELEVENLABS_VOICE_ID


def nemotron_configured() -> bool:
    return _nvidia_api_key() is not None


def elevenlabs_configured() -> bool:
    return _elevenlabs_api_key() is not None


def _openai_available() -> bool:
    try:
        from openai import OpenAI  # noqa: F401
    except Exception:
        return False
    return True


def _normalize_json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): _normalize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_json_value(item) for item in value]
    return str(value)


def _read_session_events() -> list[dict[str, Any]]:
    if not SESSION_LOG_PATH.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in SESSION_LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _current_session_events() -> list[dict[str, Any]]:
    session_id = _session_id()
    return [event for event in _read_session_events() if event.get("session_id") == session_id]


def _append_raw_event(entry: dict[str, Any]) -> None:
    _runtime_path_ready()
    with _WRITE_LOCK:
        with SESSION_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def _ensure_session_started() -> dict[str, Any]:
    events = _current_session_events()
    for event in events:
        if event.get("event_type") == "session_started":
            return event

    started_event = {
        "timestamp": _iso_now(),
        "session_id": _session_id(),
        "event_type": "session_started",
        "payload": {
            "target_minutes": TARGET_MINUTES,
            "log_file": str(SESSION_LOG_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
    }
    _append_raw_event(started_event)
    return started_event


def append_event(event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_session_started()
    entry = {
        "timestamp": _iso_now(),
        "session_id": _session_id(),
        "event_type": event_type,
        "payload": _normalize_json_value(payload),
    }
    _append_raw_event(entry)
    return entry


def load_recent_events(limit: int = 100) -> list[dict[str, Any]]:
    events = _current_session_events()
    return events[-max(1, limit) :]


def _event_summary(event: dict[str, Any]) -> str:
    timestamp = str(event.get("timestamp") or "unknown-time")
    event_type = str(event.get("event_type") or "event")
    payload = event.get("payload")
    if isinstance(payload, dict):
        if isinstance(payload.get("message"), str) and payload["message"].strip():
            return f"[{timestamp}] {event_type}: {payload['message'].strip()}"
        if isinstance(payload.get("reply"), str) and payload["reply"].strip():
            return f"[{timestamp}] {event_type}: {payload['reply'].strip()}"
    return f"[{timestamp}] {event_type}: {json.dumps(payload, ensure_ascii=True)}"


def build_memory_context() -> str:
    _ensure_session_started()
    lines: list[str] = []
    for event in load_recent_events(MAX_MEMORY_EVENTS):
        lines.append(_event_summary(event))

    memory_context = "\n".join(lines)
    if len(memory_context) > MAX_MEMORY_CHARS:
        memory_context = memory_context[-MAX_MEMORY_CHARS:]
    return memory_context


def _fallback_reply(user_message: str, memory_context: str) -> str:
    lowered = user_message.lower()
    if "what happened earlier" in lowered or "remember" in lowered or "earlier in this session" in lowered:
        if memory_context.strip():
            recent_lines = [line for line in memory_context.splitlines() if line.strip()][-5:]
            return "Recent session events: " + " | ".join(recent_lines)
        return "I do not know yet because the session log is empty."

    if memory_context.strip():
        recent_lines = [line for line in memory_context.splitlines() if line.strip()][-3:]
        return (
            "Nemotron is unavailable, but the session log is active. "
            "Recent context: " + " | ".join(recent_lines)
        )

    return "Nemotron is unavailable and the session log is still empty, so I do not know yet."


def call_nemotron_with_memory(user_message: str, memory_context: str) -> dict[str, Any]:
    if not nemotron_configured() or not _openai_available():
        return {
            "source": "fallback",
            "reply": _fallback_reply(user_message, memory_context),
            "memory_used": bool(memory_context.strip()),
            "model": _nim_model(),
            "fallback_reason": None if nemotron_configured() else "nvidia_api_key_missing",
        }

    try:
        from openai import OpenAI

        client = OpenAI(base_url=_nim_base_url(), api_key=_nvidia_api_key(), timeout=_nim_timeout_seconds())
        completion = client.chat.completions.create(
            model=_nim_model(),
            temperature=0.2,
            top_p=0.8,
            max_tokens=220,
            messages=[
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Current session log:\n"
                        f"{memory_context or '[no events logged yet]'}\n\n"
                        f"User message: {user_message}"
                    ),
                },
            ],
        )
        reply = completion.choices[0].message.content if completion.choices else None
        normalized_reply = " ".join(str(reply or "").split()).strip()
        if not normalized_reply:
            raise ValueError("Nemotron returned an empty response")
        return {
            "source": "nvidia-nemotron",
            "reply": normalized_reply,
            "memory_used": bool(memory_context.strip()),
            "model": _nim_model(),
            "fallback_reason": None,
        }
    except Exception as exc:
        return {
            "source": "fallback",
            "reply": _fallback_reply(user_message, memory_context),
            "memory_used": bool(memory_context.strip()),
            "model": _nim_model(),
            "fallback_reason": type(exc).__name__,
        }


def call_elevenlabs_tts(text: str) -> dict[str, Any]:
    if not text.strip() or not elevenlabs_configured():
        return {
            "audio_available": False,
            "audio_url": None,
            "filename": None,
        }

    _runtime_path_ready()
    voice_id = _elevenlabs_voice_id()
    assert voice_id is not None
    body = json.dumps(
        {
            "text": text,
            "model_id": DEFAULT_ELEVENLABS_MODEL,
            "output_format": "mp3_44100_128",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=body,
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": _elevenlabs_api_key() or "",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            audio_bytes = response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return {
            "audio_available": False,
            "audio_url": None,
            "filename": None,
        }

    filename = f"voice-agent-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}.mp3"
    output_path = AUDIO_DIR / filename
    output_path.write_bytes(audio_bytes)
    return {
        "audio_available": True,
        "audio_url": f"/api/v1/voice-agent/audio/{filename}",
        "filename": filename,
    }


def get_audio_file_path(filename: str) -> Path | None:
    candidate = (AUDIO_DIR / filename).resolve()
    try:
        candidate.relative_to(AUDIO_DIR.resolve())
    except ValueError:
        return None
    return candidate if candidate.exists() and candidate.is_file() else None


def _session_started_at() -> datetime:
    started_event = _ensure_session_started()
    try:
        return datetime.fromisoformat(str(started_event["timestamp"]))
    except Exception:
        return _utc_now()


def _uptime_minutes() -> int:
    delta = _utc_now() - _session_started_at()
    return max(0, int(delta.total_seconds() // 60))


def voice_agent_status() -> dict[str, Any]:
    _ensure_session_started()
    events = _current_session_events()
    return {
        "status": "running",
        "session_id": _session_id(),
        "started_at": _session_started_at().isoformat(),
        "uptime_minutes": _uptime_minutes(),
        "target_minutes": TARGET_MINUTES,
        "events_logged": len(events),
        "nemotron_configured": nemotron_configured(),
        "elevenlabs_configured": elevenlabs_configured(),
        "session_logging_active": True,
    }


def voice_agent_session(limit: int = 100) -> dict[str, Any]:
    return {
        "session_id": _session_id(),
        "events": load_recent_events(limit),
        "events_logged": len(_current_session_events()),
    }


def voice_agent_evidence() -> dict[str, Any]:
    status = voice_agent_status()
    return {
        "session_started_at": status["started_at"],
        "current_time": _iso_now(),
        "uptime_minutes": status["uptime_minutes"],
        "target_minutes": TARGET_MINUTES,
        "target_met": status["uptime_minutes"] >= TARGET_MINUTES,
        "events_logged": status["events_logged"],
        "log_file": str(SESSION_LOG_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


def record_voice_agent_event(event_type: str, message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {"message": message}
    if extra:
        payload.update(extra)
    entry = append_event(event_type, payload)
    return {
        "status": "ok",
        "event": entry,
        "events_logged": len(_current_session_events()),
    }


def handle_voice_agent_message(message: str) -> dict[str, Any]:
    append_event("user_message", {"message": message})
    memory_context = build_memory_context()
    assistant_response = call_nemotron_with_memory(message, memory_context)
    audio_result = call_elevenlabs_tts(assistant_response["reply"])

    append_event(
        "assistant_message",
        {
            "message": message,
            "reply": assistant_response["reply"],
            "source": assistant_response["source"],
            "memory_used": assistant_response["memory_used"],
            "audio_url": audio_result["audio_url"],
        },
    )

    return {
        "source": assistant_response["source"],
        "reply": assistant_response["reply"],
        "memory_used": assistant_response["memory_used"],
        "events_logged": len(_current_session_events()),
        "audio_available": audio_result["audio_available"],
        "audio_url": audio_result["audio_url"],
        "fallback_reason": assistant_response.get("fallback_reason"),
    }


def export_voice_agent_artifacts(destination: Path) -> dict[str, Any]:
    _runtime_path_ready()
    destination.mkdir(parents=True, exist_ok=True)
    exported_files: list[str] = []

    if SESSION_LOG_PATH.exists():
        target = destination / SESSION_LOG_PATH.name
        shutil.copy2(SESSION_LOG_PATH, target)
        exported_files.append(target.name)

    manifest_path = destination / "audio_manifest.json"
    manifest = []
    for audio_file in sorted(AUDIO_DIR.glob("*.mp3")):
        target_audio = destination / audio_file.name
        shutil.copy2(audio_file, target_audio)
        manifest.append({"filename": audio_file.name, "size_bytes": audio_file.stat().st_size})
        exported_files.append(target_audio.name)

    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    exported_files.append(manifest_path.name)
    return {
        "destination": str(destination),
        "files": exported_files,
    }