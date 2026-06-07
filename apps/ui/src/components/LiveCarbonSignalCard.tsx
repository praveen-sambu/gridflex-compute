"use client";

import { useEffect, useState } from "react";

import type { LiveCarbonSignalResponse } from "@/types/gridflex";

const DEFAULT_API_BASE_URL = "http://scan-12.local:8000";
const FALLBACK_MESSAGE = "Live carbon signal unavailable; using GridFlex forecast.";

type LiveCarbonSignalCardProps = {
  apiBaseUrl?: string | null;
  initialSignal?: LiveCarbonSignalResponse | null;
  disableLiveFetch?: boolean;
};

function formatTimeWindow(value: string | null | undefined) {
  if (!value) {
    return "—";
  }

  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC"
  }).format(new Date(value));
}

function normalizeBaseUrl(apiBaseUrl?: string | null) {
  return (apiBaseUrl?.trim() || DEFAULT_API_BASE_URL).replace(/\/$/, "");
}

export function LiveCarbonSignalCard({ apiBaseUrl, initialSignal = null, disableLiveFetch = false }: LiveCarbonSignalCardProps) {
  const [signal, setSignal] = useState<LiveCarbonSignalResponse | null>(initialSignal);
  const [message, setMessage] = useState(
    initialSignal ? (initialSignal.status === "ok" ? `Live carbon signal from ${initialSignal.source}.` : FALLBACK_MESSAGE) : disableLiveFetch ? FALLBACK_MESSAGE : "Checking live carbon signal...",
  );

  useEffect(() => {
    if (initialSignal || disableLiveFetch) {
      return;
    }

    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 6500);

    async function loadLiveCarbonSignal() {
      try {
        const response = await fetch(`${normalizeBaseUrl(apiBaseUrl)}/api/v1/live-carbon`, {
          cache: "no-store",
          signal: controller.signal
        });

        if (!response.ok) {
          throw new Error(`Live carbon request failed with status ${response.status}`);
        }

        const payload = (await response.json()) as LiveCarbonSignalResponse;
        setSignal(payload);
        setMessage(payload.status === "ok" ? `Live carbon signal from ${payload.source}.` : FALLBACK_MESSAGE);
      } catch {
        setSignal(null);
        setMessage(FALLBACK_MESSAGE);
      } finally {
        window.clearTimeout(timeoutId);
      }
    }

    loadLiveCarbonSignal();

    return () => {
      controller.abort();
      window.clearTimeout(timeoutId);
    };
  }, [apiBaseUrl, disableLiveFetch, initialSignal]);

  const intensityText = typeof signal?.current_intensity === "number" ? `${signal.current_intensity} gCO2/kWh` : "Unavailable";
  const recommendation = signal?.recommendation ?? "use_gridflex_forecast";
  const operatorMessage = signal?.operator_message ?? FALLBACK_MESSAGE;

  return (
    <section className="panel live-carbon-card" aria-live="polite">
      <div className="live-carbon-header">
        <div>
          <p className="section-kicker">carbon telemetry</p>
          <h2>Live carbon signal</h2>
          <p className="live-carbon-status">{message}</p>
        </div>
        <span className={`pill live-carbon-pill ${recommendation}`}>{recommendation.replaceAll("_", " ")}</span>
      </div>

      <div className="live-carbon-grid">
        <article>
          <span>Current intensity</span>
          <strong>{intensityText}</strong>
        </article>
        <article>
          <span>Index</span>
          <strong>{signal?.index ?? "unknown"}</strong>
        </article>
        <article>
          <span>Window</span>
          <strong>
            {formatTimeWindow(signal?.from)} - {formatTimeWindow(signal?.to)}
          </strong>
        </article>
      </div>

      <div className="live-carbon-hero-strip">
        <div className="live-carbon-hero-value">
          <span>Run window</span>
          <strong>{recommendation.replaceAll("_", " ")}</strong>
        </div>
        <div className="live-carbon-hero-copy">
          <span>Decision story</span>
          <p>{signal?.reason ?? FALLBACK_MESSAGE}</p>
        </div>
      </div>

      <p className="live-carbon-reason">{signal?.reason ?? FALLBACK_MESSAGE}</p>

      <div className="voice-ready-box live-carbon-callout">
        <strong>Operator callout</strong>
        <p>{operatorMessage}</p>
      </div>
    </section>
  );
}