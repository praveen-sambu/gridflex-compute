"use client";

import { useEffect, useState } from "react";

import type { LiveCarbonSignalResponse } from "@/types/gridflex";

const DEFAULT_API_BASE_URL = "http://scan-12.local:8000";
const FALLBACK_MESSAGE = "Live carbon signal unavailable; using GridFlex forecast.";

type LiveCarbonSignalCardProps = {
  apiBaseUrl?: string | null;
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

export function LiveCarbonSignalCard({ apiBaseUrl }: LiveCarbonSignalCardProps) {
  const [signal, setSignal] = useState<LiveCarbonSignalResponse | null>(null);
  const [message, setMessage] = useState("Checking live carbon signal...");

  useEffect(() => {
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
  }, [apiBaseUrl]);

  const intensityText = typeof signal?.current_intensity === "number" ? `${signal.current_intensity} gCO2/kWh` : "Unavailable";
  const recommendation = signal?.recommendation ?? "use_gridflex_forecast";
  const operatorMessage = signal?.operator_message ?? FALLBACK_MESSAGE;

  return (
    <section className="panel live-carbon-card" aria-live="polite">
      <div className="live-carbon-header">
        <div>
          <h2>Live Carbon Signal</h2>
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

      <p className="live-carbon-reason">{signal?.reason ?? FALLBACK_MESSAGE}</p>

      <div className="voice-ready-box">
        <strong>Voice-ready explanation</strong>
        <p>{operatorMessage}</p>
      </div>
    </section>
  );
}