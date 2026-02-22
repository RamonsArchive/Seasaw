"use client";

interface ScoreBadgeProps {
  score: number;
  grade: string;
}

function getGradeColor(grade: string): string {
  const colors: Record<string, string> = {
    A: "#22c55e",
    B: "#84cc16",
    C: "#eab308",
    D: "#f97316",
    F: "#ef4444",
  };
  return colors[grade] || "#6b7280";
}

export default function ScoreBadge({ score, grade }: ScoreBadgeProps) {
  const color = getGradeColor(grade);
  const circumference = 2 * Math.PI * 54; // radius 54
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="score-badge">
      <svg className="score-ring" viewBox="0 0 120 120">
        {/* Background ring */}
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          opacity="0.1"
        />
        {/* Score arc */}
        <circle
          cx="60"
          cy="60"
          r="54"
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="score-ring-progress"
          style={{
            "--target-offset": `${offset}px`,
            "--circumference": `${circumference}px`,
          } as React.CSSProperties}
        />
      </svg>
      <div className="score-badge-inner">
        <span className="score-number" style={{ color }}>
          {score}
        </span>
        <span className="score-grade" style={{ color }}>
          {grade}
        </span>
      </div>
    </div>
  );
}
