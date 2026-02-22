"use server";

import type { AnalyzeResponse } from "./types";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function analyzeService(
  query: string
): Promise<AnalyzeResponse> {
  const trimmed = query.trim();
  if (!trimmed) {
    throw new Error("Please enter a service name to analyze.");
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 120_000); // 2 min timeout

  try {
    const res = await fetch(`${BACKEND_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: trimmed }),
      signal: controller.signal,
      cache: "no-store",
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(
        body.detail || `Backend returned ${res.status}: ${res.statusText}`
      );
    }

    const data: AnalyzeResponse = await res.json();
    return data;
  } catch (err: unknown) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "Analysis timed out. The service might be taking too long to respond."
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}
