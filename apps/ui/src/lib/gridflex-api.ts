import { access, readFile } from "node:fs/promises";
import path from "node:path";

import type { CarbonOrchestrationResponse, ControlLoopDemoResponse, DemoReadinessResponse, GridFlexResponse } from "@/types/gridflex";

export type DemoDataResult = {
  data: GridFlexResponse;
  source: "api" | "mock";
  apiBaseUrl: string | null;
  error: string | null;
};

export type CarbonOrchestrationDataResult = {
  data: CarbonOrchestrationResponse | null;
  source: "api" | "unavailable";
  apiBaseUrl: string | null;
  error: string | null;
};

export type ControlLoopDashboardDataResult = {
  controlLoop: ControlLoopDemoResponse | null;
  readiness: DemoReadinessResponse | null;
  source: "api" | "unavailable";
  apiBaseUrl: string | null;
  error: string | null;
};

const DEFAULT_API_BASE_URL = "http://scan-12.local:8000";
const FALLBACK_API_BASE_URL = "http://localhost:8000";

async function firstExistingPath(paths: string[]) {
  for (const filePath of paths) {
    try {
      await access(filePath);
      return filePath;
    } catch {
      // Try the next project-root candidate.
    }
  }

  throw new Error(`Could not find demo response JSON. Tried: ${paths.join(", ")}`);
}

async function loadMockData(): Promise<GridFlexResponse> {
  const demoPath = await firstExistingPath([
    path.join(/*turbopackIgnore: true*/ process.cwd(), "..", "..", "data", "mock", "gridflex_demo_response.json"),
    path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "mock", "gridflex_demo_response.json")
  ]);
  const raw = await readFile(demoPath, "utf8");

  return JSON.parse(raw) as GridFlexResponse;
}

function resolveBaseUrls() {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_GRIDFLEX_API_BASE_URL?.trim();

  if (configuredBaseUrl) {
    return [configuredBaseUrl];
  }

  return [DEFAULT_API_BASE_URL, FALLBACK_API_BASE_URL];
}

async function fetchJsonFromApi<T>(baseUrl: string, route: string): Promise<T> {
  const response = await fetch(`${baseUrl}${route}`, {
    cache: "no-store"
  });

  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function getDemoData(): Promise<DemoDataResult> {
  const attemptedErrors: string[] = [];

  for (const baseUrl of resolveBaseUrls()) {
    try {
      const data = await fetchJsonFromApi<GridFlexResponse>(baseUrl, "/api/v1/demo");

      return {
        data,
        source: "api",
        apiBaseUrl: baseUrl,
        error: null
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      attemptedErrors.push(`${baseUrl}: ${message}`);
    }
  }

  const fallbackData = await loadMockData();

  return {
    data: fallbackData,
    source: "mock",
    apiBaseUrl: resolveBaseUrls()[0] ?? null,
    error: attemptedErrors.join("; ") || "API unavailable"
  };
}

export async function getCarbonOrchestrationDemoData(): Promise<CarbonOrchestrationDataResult> {
  const attemptedErrors: string[] = [];

  for (const baseUrl of resolveBaseUrls()) {
    try {
      const data = await fetchJsonFromApi<CarbonOrchestrationResponse>(baseUrl, "/api/v1/carbon-orchestration-demo");

      return {
        data,
        source: "api",
        apiBaseUrl: baseUrl,
        error: null
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      attemptedErrors.push(`${baseUrl}: ${message}`);
    }
  }

  return {
    data: null,
    source: "unavailable",
    apiBaseUrl: resolveBaseUrls()[0] ?? null,
    error: attemptedErrors.join("; ") || "API unavailable"
  };
}

export async function getControlLoopDashboardData(): Promise<ControlLoopDashboardDataResult> {
  const attemptedErrors: string[] = [];

  for (const baseUrl of resolveBaseUrls()) {
    try {
      const [controlLoop, readiness] = await Promise.all([
        fetchJsonFromApi<ControlLoopDemoResponse>(baseUrl, "/api/v1/control-loop-demo"),
        fetchJsonFromApi<DemoReadinessResponse>(baseUrl, "/api/v1/demo-readiness")
      ]);

      return {
        controlLoop,
        readiness,
        source: "api",
        apiBaseUrl: baseUrl,
        error: null
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      attemptedErrors.push(`${baseUrl}: ${message}`);
    }
  }

  return {
    controlLoop: null,
    readiness: null,
    source: "unavailable",
    apiBaseUrl: resolveBaseUrls()[0] ?? null,
    error: attemptedErrors.join("; ") || "API unavailable"
  };
}