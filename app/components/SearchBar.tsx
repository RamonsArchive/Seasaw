"use client";

import { useState, useRef } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  isLoading: boolean;
}

export default function SearchBar({ onSearch, isLoading }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} className="search-bar-form">
      <div className="search-input-wrapper">
        {/* Search icon */}
        <svg
          className="search-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>

        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search any service… Netflix, Spotify, Instagram…"
          className="search-input"
          disabled={isLoading}
          autoFocus
        />

        <button
          type="submit"
          className="search-button"
          disabled={!query.trim() || isLoading}
        >
          {isLoading ? (
            <span className="spinner" />
          ) : (
            "Analyze"
          )}
        </button>
      </div>
    </form>
  );
}
