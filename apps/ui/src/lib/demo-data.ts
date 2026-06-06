import { access, readFile } from "node:fs/promises";
import path from "node:path";

import type { GridFlexResponse } from "@/types/gridflex";

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

export async function getDemoData(): Promise<GridFlexResponse> {
  const demoPath = await firstExistingPath([
    path.join(/*turbopackIgnore: true*/ process.cwd(), "..", "..", "data", "mock", "gridflex_demo_response.json"),
    path.join(/*turbopackIgnore: true*/ process.cwd(), "data", "mock", "gridflex_demo_response.json")
  ]);
  const raw = await readFile(demoPath, "utf8");

  return JSON.parse(raw) as GridFlexResponse;
}