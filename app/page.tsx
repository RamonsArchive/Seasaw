"use client";

import { useState, useTransition } from "react";
import SearchBar from "./components/SearchBar";
import ServiceGrid from "./components/ServiceGrid";
import NutritionLabel from "./components/NutritionLabel";
import LoadingSkeleton from "./components/LoadingSkeleton";
import Navbar from "./components/Navbar";
import { analyzeService } from "./actions";
import type { AnalyzeResponse } from "./types";

export default function Home() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [activeQuery, setActiveQuery] = useState<string>("");

  const handleSearch = (query: string) => {
    setError(null);
    setResult(null);
    setActiveQuery(query);

    startTransition(async () => {
      try {
        const data = await analyzeService(query);
        setResult(data);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "An unexpected error occurred.";
        setError(message);
      }
    });
  };

  return (
    <div className="page">
      <Navbar />
      {/* Ambient background glow */}
      <div className="ambient-glow" />

      <main className="main">
        {/* Hero */}
        <section className="hero">
          <div className="hero-badge">
            <span className="hero-badge-dot" />
            Powered by local AI — your data never leaves your machine
          </div>
          <h1 className="hero-title">
            Know What You&apos;re
            <br />
            <span className="hero-accent">Agreeing To</span>
          </h1>
          <p className="hero-subtitle">
            Seasaw reads the Terms of Service and Privacy Policies you never do,
            then gives every service a TrustScore so you can make informed decisions.
          </p>
        </section>

        {/* Search */}
        <SearchBar onSearch={handleSearch} isLoading={isPending} />

        {/* Preset services */}
        {!result && !isPending && (
          <ServiceGrid onSelect={handleSearch} isLoading={isPending} />
        )}

        {/* Loading */}
        {isPending && (
          <section className="results-section">
            <p className="analyzing-text">
              <span className="spinner" /> Analyzing <strong>{activeQuery}</strong>…
              This may take 30–60 seconds.
            </p>
            <LoadingSkeleton />
          </section>
        )}

        {/* Error */}
        {error && !isPending && (
          <section className="results-section">
            <div className="error-card">
              <span className="error-icon">⚠️</span>
              <div>
                <p className="error-title">Analysis Failed</p>
                <p className="error-message">{error}</p>
              </div>
            </div>
          </section>
        )}

        {/* Result */}
        {result && !isPending && (
          <section className="results-section">
            <NutritionLabel data={result} />
            <button
              className="search-again-btn"
              onClick={() => {
                setResult(null);
                setError(null);
                setActiveQuery("");
              }}
            >
              ← Analyze another service
            </button>
          </section>
        )}
      </main>

      {/* Footer */}
      <footer className="site-footer">
        <p>
          Seasaw — An open-source project. Analysis is performed locally using AI.
          Results are informational and not legal advice.
        </p>
      </footer>
    </div>
  );
}
