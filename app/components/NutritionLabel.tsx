"use client";

import { useState } from "react";
import type { AnalyzeResponse, PolicyAttribute } from "../types";
import ScoreBadge from "./ScoreBadge";

interface NutritionLabelProps {
  data: AnalyzeResponse;
}

/* ---- Category grouping (Apple-style) ---- */
const CATEGORIES: { title: string; icon: string; ids: string[] }[] = [
  {
    title: "Data Practices",
    icon: "🔐",
    ids: ["data_selling", "data_sharing", "third_party_tracking"],
  },
  {
    title: "Your Rights",
    icon: "👤",
    ids: ["account_deletion", "class_action_waiver", "arbitration_clause"],
  },
  {
    title: "Security & Retention",
    icon: "🛡️",
    ids: ["encryption", "data_retention", "government_requests"],
  },
  {
    title: "Legal Terms",
    icon: "📋",
    ids: ["unilateral_changes", "liability_limitation", "content_license"],
  },
];

function SeverityDot({ severity }: { severity: string }) {
  const label =
    severity === "good" ? "Good" : severity === "bad" ? "Concern" : "Unclear";
  return (
    <span className={`severity-dot severity-${severity}`} title={label}>
      <span className="severity-dot-inner" />
    </span>
  );
}

function SeverityIcon({ severity }: { severity: string }) {
  switch (severity) {
    case "good":
      return <span className="severity-icon severity-good">✓</span>;
    case "neutral":
      return <span className="severity-icon severity-neutral">–</span>;
    case "bad":
      return <span className="severity-icon severity-bad">!</span>;
    default:
      return <span className="severity-icon">?</span>;
  }
}

function SeverityBar({ score }: { score: number }) {
  const color =
    score >= 70 ? "var(--good)" : score >= 40 ? "var(--neutral)" : "var(--bad)";
  return (
    <div className="severity-bar-track">
      <div
        className="severity-bar-fill"
        style={{ width: `${score}%`, background: color }}
      />
    </div>
  );
}

function AttributeRow({ attr }: { attr: PolicyAttribute }) {
  const [expanded, setExpanded] = useState(false);
  const fillPercent =
    attr.weight > 0 ? (attr.points_earned / attr.weight) * 100 : 0;

  return (
    <div className={`attr-row`}>
      <button
        className="attr-row-header"
        onClick={() => setExpanded(!expanded)}
        aria-expanded={expanded}
      >
        <div className="attr-row-left">
          <SeverityIcon severity={attr.severity} />
          <div className="attr-info">
            <span className="attr-label">{attr.label}</span>
            <span className="attr-value-inline">{attr.value}</span>
          </div>
        </div>
        <div className="attr-row-right">
          <div className="attr-score-group">
            <SeverityBar score={fillPercent} />
            <span className="attr-points">
              {attr.points_earned}/{attr.weight}
            </span>
          </div>
          <svg
            className={`attr-chevron ${expanded ? "attr-chevron-open" : ""}`}
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
      </button>
      {expanded && (
        <div className="attr-evidence">
          <div className="evidence-content">
            <span className="evidence-label">Evidence</span>
            <p>{attr.evidence}</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreBreakdown({ data }: { data: AnalyzeResponse }) {
  const totalPossible = data.attributes.reduce((sum, a) => sum + a.weight, 0);
  const totalEarned = data.attributes.reduce(
    (sum, a) => sum + a.points_earned,
    0
  );

  return (
    <div className="score-breakdown">
      <div className="breakdown-bar-track">
        <div
          className="breakdown-bar-fill"
          style={{
            width: `${(totalEarned / totalPossible) * 100}%`,
          }}
        />
      </div>
      <div className="breakdown-labels">
        <span>
          <strong>{totalEarned.toFixed(1)}</strong> of {totalPossible} points
        </span>
        <span>{data.trust_score}/100 overall</span>
      </div>
    </div>
  );
}

function CategorySection({
  title,
  icon,
  attributes,
}: {
  title: string;
  icon: string;
  attributes: PolicyAttribute[];
}) {
  if (attributes.length === 0) return null;

  const catGood = attributes.filter((a) => a.severity === "good").length;
  const catBad = attributes.filter((a) => a.severity === "bad").length;

  return (
    <div className="category-section">
      <div className="category-header">
        <span className="category-icon">{icon}</span>
        <span className="category-title">{title}</span>
        <div className="category-dots">
          {attributes.map((a) => (
            <SeverityDot key={a.id} severity={a.severity} />
          ))}
        </div>
      </div>
      <div className="category-attrs">
        {attributes.map((attr) => (
          <AttributeRow key={attr.id} attr={attr} />
        ))}
      </div>
    </div>
  );
}

export default function NutritionLabel({ data }: NutritionLabelProps) {
  const goodCount = data.attributes.filter((a) => a.severity === "good").length;
  const badCount = data.attributes.filter((a) => a.severity === "bad").length;
  const neutralCount = data.attributes.filter(
    (a) => a.severity === "neutral"
  ).length;

  // Build attribute map for category lookup
  const attrMap = new Map(data.attributes.map((a) => [a.id, a]));

  return (
    <div className="nutrition-label">
      {/* Header */}
      <div className="nl-header">
        <div className="nl-header-info">
          <h2 className="nl-service-name">{data.service_name}</h2>
          <a
            href={`https://${data.domain}`}
            target="_blank"
            rel="noopener noreferrer"
            className="nl-domain"
          >
            {data.domain} ↗
          </a>
          <div className="nl-summary-pills">
            {goodCount > 0 && (
              <span className="pill pill-good">
                {goodCount} positive
              </span>
            )}
            {neutralCount > 0 && (
              <span className="pill pill-neutral">
                {neutralCount} unclear
              </span>
            )}
            {badCount > 0 && (
              <span className="pill pill-bad">
                {badCount} concern{badCount > 1 ? "s" : ""}
              </span>
            )}
          </div>
        </div>
        <ScoreBadge score={data.trust_score} grade={data.grade} />
      </div>

      {/* Score breakdown */}
      <ScoreBreakdown data={data} />

      {/* Divider */}
      <div className="nl-divider-thick" />

      {/* Categories — Apple-style grouped sections */}
      {CATEGORIES.map((cat) => {
        const catAttrs = cat.ids
          .map((id) => attrMap.get(id))
          .filter((a): a is PolicyAttribute => a !== undefined);
        return (
          <CategorySection
            key={cat.title}
            title={cat.title}
            icon={cat.icon}
            attributes={catAttrs}
          />
        );
      })}

      {/* Footer */}
      <div className="nl-footer">
        <div className="nl-footer-links">
          {data.terms_url && (
            <a
              href={data.terms_url}
              target="_blank"
              rel="noopener noreferrer"
              className="nl-source-link"
            >
              📄 Terms of Service
            </a>
          )}
          {data.privacy_url && (
            <a
              href={data.privacy_url}
              target="_blank"
              rel="noopener noreferrer"
              className="nl-source-link"
            >
              🔒 Privacy Policy
            </a>
          )}
        </div>
        <p className="nl-timestamp">
          Analyzed{" "}
          {new Date(data.analyzed_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}
