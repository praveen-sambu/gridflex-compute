"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import type {
  VoiceAgentEvidenceResponse,
  VoiceAgentEvent,
  VoiceAgentMessageResponse,
  VoiceAgentSessionResponse,
  VoiceAgentStatusResponse,
} from "@/types/gridflex";

type VoiceAgentDashboardProps = {
  status: VoiceAgentStatusResponse | null;
  session: VoiceAgentSessionResponse | null;
  evidence: VoiceAgentEvidenceResponse | null;
  apiBaseUrl?: string | null;
  error?: string | null;
};

type LatestResponseMeta = {
  question: string;
  source: string;
  memoryUsed: boolean;
  audioAvailable: boolean;
  fallbackReason?: string | null;
};

type SpeechRecognitionResultLike = {
  results: ArrayLike<{
    0: { transcript: string };
    isFinal: boolean;
    length: number;
  }>;
};

type BrowserSpeechRecognition = {
  lang: string;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: SpeechRecognitionResultLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
};

type SpeechRecognitionConstructor = new () => BrowserSpeechRecognition;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

const DEFAULT_API_BASE_URL = "http://scan-12.local:8000";

function normalizeBaseUrl(apiBaseUrl?: string | null) {
  return (apiBaseUrl?.trim() || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

function formatUtcDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const day = String(date.getUTCDate()).padStart(2, "0");
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const year = date.getUTCFullYear();
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  const seconds = String(date.getUTCSeconds()).padStart(2, "0");

  return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds} UTC`;
}

function formatDuration(totalSeconds: number) {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
}

function eventPreview(event: VoiceAgentEvent) {
  const payload = event.payload ?? {};
  const message = typeof payload.message === "string" ? payload.message : null;
  const reply = typeof payload.reply === "string" ? payload.reply : null;

  if (message) {
    return message;
  }
  if (reply) {
    return reply;
  }
  return JSON.stringify(payload);
}

async function fetchVoiceAgentSnapshot(baseUrl: string) {
  const [statusResponse, sessionResponse, evidenceResponse] = await Promise.all([
    fetch(`${baseUrl}/api/v1/voice-agent/status`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/voice-agent/session`, { cache: "no-store" }),
    fetch(`${baseUrl}/api/v1/voice-agent/evidence`, { cache: "no-store" }),
  ]);

  if (!statusResponse.ok || !sessionResponse.ok || !evidenceResponse.ok) {
    throw new Error("Voice-agent snapshot request failed.");
  }

  const [status, session, evidence] = (await Promise.all([
    statusResponse.json(),
    sessionResponse.json(),
    evidenceResponse.json(),
  ])) as [VoiceAgentStatusResponse, VoiceAgentSessionResponse, VoiceAgentEvidenceResponse];

  return { status, session, evidence };
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <article className="status-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function StatusBadge({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="readiness-item">
      <span>{label}</span>
      <span className={`pill ${ok ? "ok" : "fallback"}`}>{ok ? "ready" : "not ready"}</span>
    </div>
  );
}

function StatusTag({ label, tone = "default" }: { label: string; tone?: "default" | "ok" | "warn" | "info" }) {
  return <span className={`status-tag ${tone}`}>{label}</span>;
}

export function VoiceAgentDashboard({
  status,
  session,
  evidence,
  apiBaseUrl,
  error,
}: VoiceAgentDashboardProps) {
  const baseUrl = normalizeBaseUrl(apiBaseUrl);
  const [statusState, setStatusState] = useState(status);
  const [sessionState, setSessionState] = useState(session);
  const [evidenceState, setEvidenceState] = useState(evidence);
  const [input, setInput] = useState("");
  const [reply, setReply] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [latestResponse, setLatestResponse] = useState<LatestResponseMeta | null>(null);
  const [feedback, setFeedback] = useState<string | null>(error ?? null);
  const [busy, setBusy] = useState(false);
  const [micSupported, setMicSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(
    status?.started_at ? Math.max(0, Math.floor((Date.now() - new Date(status.started_at).getTime()) / 1000)) : 0,
  );
  const recognitionRef = useRef<BrowserSpeechRecognition | null>(null);

  useEffect(() => {
    const ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setMicSupported(Boolean(ctor));
  }, []);

  useEffect(() => {
    if (!statusState?.started_at) {
      return;
    }

    const updateElapsed = () => {
      setElapsedSeconds(Math.max(0, Math.floor((Date.now() - new Date(statusState.started_at).getTime()) / 1000)));
    };

    updateElapsed();
    const timerId = window.setInterval(updateElapsed, 1000);
    return () => window.clearInterval(timerId);
  }, [statusState?.started_at]);

  async function refreshEvidence() {
    try {
      setBusy(true);
      const snapshot = await fetchVoiceAgentSnapshot(baseUrl);
      setStatusState(snapshot.status);
      setSessionState(snapshot.session);
      setEvidenceState(snapshot.evidence);
      setFeedback("Voice-agent evidence refreshed.");
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : String(caughtError);
      setFeedback(message);
    } finally {
      setBusy(false);
    }
  }

  async function handleLogDemoEvent() {
    try {
      setBusy(true);
      const response = await fetch(`${baseUrl}/api/v1/voice-agent/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: "demo_event",
          message: "The GridFlex voice-agent dashboard log button was pressed.",
        }),
      });

      if (!response.ok) {
        throw new Error(`Voice-agent event failed with status ${response.status}`);
      }

      await refreshEvidence();
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : String(caughtError);
      setFeedback(message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSendMessage(messageOverride?: string) {
    const message = (messageOverride ?? input).trim();
    if (!message) {
      return;
    }

    try {
      setBusy(true);
      setFeedback("Sending message to the GridFlex voice agent...");
      const response = await fetch(`${baseUrl}/api/v1/voice-agent/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });
      if (!response.ok) {
        throw new Error(`Voice-agent message failed with status ${response.status}`);
      }

      const payload = (await response.json()) as VoiceAgentMessageResponse;
      setReply(payload.reply);
      setAudioUrl(payload.audio_url ? `${baseUrl}${payload.audio_url}` : null);
      setLatestResponse({
        question: message,
        source: payload.source,
        memoryUsed: payload.memory_used,
        audioAvailable: payload.audio_available,
        fallbackReason: payload.fallback_reason,
      });
      setFeedback(payload.source === "nvidia-nemotron" ? "Nemotron response received." : "Fallback response received.");
      setInput("");

      if (payload.audio_url) {
        const player = new Audio(`${baseUrl}${payload.audio_url}`);
        void player.play().catch(() => {
          // Autoplay can be blocked; the audio player remains visible below.
        });
      }

      const snapshot = await fetchVoiceAgentSnapshot(baseUrl);
      setStatusState(snapshot.status);
      setSessionState(snapshot.session);
      setEvidenceState(snapshot.evidence);
    } catch (caughtError) {
      const errorMessage = caughtError instanceof Error ? caughtError.message : String(caughtError);
      setFeedback(errorMessage);
    } finally {
      setBusy(false);
    }
  }

  function handleAskEarlier() {
    void handleSendMessage("What happened earlier in this session?");
  }

  function handleMicCapture() {
    const ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    if (!ctor) {
      setFeedback("Browser microphone capture is not available in this browser.");
      return;
    }

    if (listening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const recognition = new ctor();
    recognition.lang = "en-GB";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim();
      if (transcript) {
        setInput(transcript);
        void handleSendMessage(transcript);
      }
    };
    recognition.onerror = (event) => {
      setFeedback(`Microphone capture error: ${event.error}`);
    };
    recognition.onend = () => {
      setListening(false);
      recognitionRef.current = null;
    };

    recognitionRef.current = recognition;
    setListening(true);
    setFeedback("Browser microphone capture started. Transcript will be sent to the backend message route.");
    recognition.start();
  }

  if (!statusState || !sessionState || !evidenceState) {
    return (
      <main className="shell">
        <div className="page-nav button-row">
          <Link className="button" href="/dashboard">
            Back to GridFlex Dashboard
          </Link>
        </div>

        <section className="hero">
          <div>
            <p className="eyebrow">voice memory agent</p>
            <h1>ElevenLabs + NVIDIA Nemotron Voice Memory Agent</h1>
            <p className="lede">An isolated bounty page for long-running session memory, Nemotron recall, and ElevenLabs voice output.</p>
          </div>
        </section>

        <section className="panel" aria-live="polite">
          <strong>Voice agent unavailable</strong>
          <p>{error ?? "The voice-agent routes are not currently reachable."}</p>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <div className="page-nav button-row">
        <Link className="button" href="/dashboard">
          Back to GridFlex Dashboard
        </Link>
      </div>

      <section className="hero">
        <div>
          <p className="eyebrow">voice memory agent</p>
          <h1>ElevenLabs + NVIDIA Nemotron Voice Memory Agent</h1>
          <p className="lede">A long-running bounty track for memory recall, voice interaction, and backend-only model integration without changing the main GridFlex demo.</p>
          <p className="hero-copy">This page is designed to prove that the agent can remember earlier events, answer from session history, and return spoken output while the main demo remains untouched.</p>
          <div className="status-tag-row">
            <StatusTag label={statusState.nemotron_configured ? "Nemotron ready" : "Nemotron fallback"} tone={statusState.nemotron_configured ? "ok" : "warn"} />
            <StatusTag label={statusState.elevenlabs_configured ? "ElevenLabs ready" : "Audio unavailable"} tone={statusState.elevenlabs_configured ? "ok" : "warn"} />
            <StatusTag label={sessionState.events_logged > 0 ? "Session memory active" : "Awaiting history"} tone="info" />
          </div>
        </div>
        <aside className="meta-card">
          Bounty target
          <strong>1 hour 11 minutes</strong>
          <br />
          Session
          <strong>{statusState.session_id}</strong>
          <br />
          Endpoint
          <strong>{baseUrl}</strong>
        </aside>
      </section>

      <section className="panel voice-agent-hero" aria-live="polite">
        <div className="live-carbon-header">
          <div>
            <p className="section-kicker">bounty timer</p>
            <h2>Session timer</h2>
            <p className="panel-subtitle">Keep this page and the backend session running for at least 71 minutes to satisfy the bounty evidence requirement.</p>
          </div>
          <span className={`pill ${evidenceState.target_met ? "ok" : "fallback"}`}>{evidenceState.target_met ? "target met" : "target running"}</span>
        </div>

        <div className="status-grid">
          <StatusCard label="Elapsed" value={formatDuration(elapsedSeconds)} />
          <StatusCard label="Events logged" value={String(statusState.events_logged)} />
          <StatusCard label="Target" value={`${statusState.target_minutes} min`} />
          <StatusCard label="Memory recall" value={sessionState.events_logged > 1 ? "available" : "warming up"} />
        </div>

        <div className="dashboard-grid voice-agent-summary-grid">
          <div className="panel voice-agent-subpanel">
            <div className="section-heading-row">
              <div>
                <p className="section-kicker">runtime status</p>
                <h2>Status badges</h2>
              </div>
            </div>
            <div className="readiness-list">
              <StatusBadge label="Nemotron configured" ok={statusState.nemotron_configured} />
              <StatusBadge label="ElevenLabs configured" ok={statusState.elevenlabs_configured} />
              <StatusBadge label="Session logging active" ok={statusState.session_logging_active} />
            </div>
          </div>

          <div className="panel voice-agent-subpanel">
            <div className="section-heading-row">
              <div>
                <p className="section-kicker">evidence bundle</p>
                <h2>Evidence</h2>
              </div>
            </div>
            <div className="readiness-list">
              <div className="readiness-item"><span>Started at</span><span>{formatUtcDateTime(evidenceState.session_started_at)}</span></div>
              <div className="readiness-item"><span>Current time</span><span>{formatUtcDateTime(evidenceState.current_time)}</span></div>
              <div className="readiness-item"><span>Log file</span><span>{evidenceState.log_file}</span></div>
              <div className="readiness-item"><span>Target met</span><span className={`pill ${evidenceState.target_met ? "ok" : "fallback"}`}>{evidenceState.target_met ? "yes" : "no"}</span></div>
            </div>
          </div>
        </div>
      </section>

      <section className="voice-agent-grid">
        <div className="stack-column">
          <section className="panel voice-chat-panel">
            <div className="live-carbon-header">
              <div>
                <p className="section-kicker">interactive console</p>
                <h2>Chat and voice I/O</h2>
                <p className="panel-subtitle">Voice input uses browser microphone capture when available. Voice output uses backend ElevenLabs audio whenever the backend returns it.</p>
              </div>
            </div>

            <div className="voice-agent-actions">
              <button className="button" type="button" onClick={handleLogDemoEvent} disabled={busy}>
                Log demo event
              </button>
              <button className="button" type="button" onClick={handleAskEarlier} disabled={busy}>
                Ask what happened earlier?
              </button>
              <button className="button" type="button" onClick={() => void refreshEvidence()} disabled={busy}>
                Refresh evidence
              </button>
              {micSupported ? (
                <button className="button primary" type="button" onClick={handleMicCapture} disabled={busy && !listening}>
                  {listening ? "Stop microphone" : "Start microphone"}
                </button>
              ) : (
                <span className="voice-agent-note">Browser microphone capture unavailable in this browser.</span>
              )}
            </div>

            <div className="voice-chat-input-row">
              <textarea
                className="voice-agent-textarea"
                rows={4}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask the agent what happened earlier, or log a live event through chat."
              />
              <button className="button primary" type="button" onClick={() => void handleSendMessage()} disabled={busy || !input.trim()}>
                {busy ? "Working..." : "Send message"}
              </button>
            </div>

            {feedback ? (
              <div className="voice-ready-box">
                <strong>Agent status</strong>
                <p>{feedback}</p>
              </div>
            ) : null}

            {latestResponse ? (
              <div className="voice-chat-transcript">
                <div className="voice-chat-bubble user">
                  <span className="voice-chat-role">User question</span>
                  <p>{latestResponse.question}</p>
                </div>

                {reply ? (
                  <div className="voice-chat-bubble assistant">
                    <div className="voice-chat-header">
                      <span className="voice-chat-role">Agent reply</span>
                      <div className="status-tag-row compact">
                        <StatusTag label={latestResponse.source === "nvidia-nemotron" ? "Nemotron" : "Fallback"} tone={latestResponse.source === "nvidia-nemotron" ? "ok" : "warn"} />
                        <StatusTag label={latestResponse.memoryUsed ? "Memory used" : "No memory used"} tone={latestResponse.memoryUsed ? "info" : "default"} />
                        <StatusTag label={latestResponse.audioAvailable ? "Audio ready" : "No audio"} tone={latestResponse.audioAvailable ? "ok" : "warn"} />
                      </div>
                    </div>
                    <p>{reply}</p>
                    {latestResponse.fallbackReason ? <p className="table-secondary">Fallback reason: {latestResponse.fallbackReason}</p> : null}
                  </div>
                ) : null}
              </div>
            ) : null}

            {audioUrl ? (
              <div className="voice-ready-box">
                <strong>Latest ElevenLabs audio</strong>
                <audio controls className="voice-agent-audio" src={audioUrl} />
              </div>
            ) : null}
          </section>
        </div>

        <div className="stack-column">
          <section className="panel">
            <div className="section-heading-row">
              <div>
                <p className="section-kicker">memory ledger</p>
                <h2>Session event log</h2>
              </div>
            </div>
            <div className="table-wrap">
              <table className="data-table data-table-relaxed">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody>
                  {sessionState.events.slice().reverse().map((event) => (
                    <tr key={`${event.timestamp}-${event.event_type}`}>
                      <td>{formatUtcDateTime(event.timestamp)}</td>
                      <td>{event.event_type}</td>
                      <td>{eventPreview(event)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}