"use client";

interface ServiceCardProps {
  name: string;
  icon: string;
  color: string;
  onClick: (name: string) => void;
  isLoading: boolean;
}

const SERVICE_PRESETS = [
  { name: "Netflix", icon: "🎬", color: "#E50914" },
  { name: "Spotify", icon: "🎵", color: "#1DB954" },
  { name: "Amazon", icon: "📦", color: "#FF9900" },
  { name: "Google", icon: "🔍", color: "#4285F4" },
  { name: "Instagram", icon: "📸", color: "#E4405F" },
  { name: "TikTok", icon: "🎶", color: "#010101" },
  { name: "Uber", icon: "🚗", color: "#000000" },
  { name: "Discord", icon: "💬", color: "#5865F2" },
];

export function ServiceCard({ name, icon, color, onClick, isLoading }: ServiceCardProps) {
  return (
    <button
      className="service-card"
      onClick={() => onClick(name)}
      disabled={isLoading}
      style={{ "--card-accent": color } as React.CSSProperties}
    >
      <span className="service-card-icon">{icon}</span>
      <span className="service-card-name">{name}</span>
    </button>
  );
}

interface ServiceGridProps {
  onSelect: (name: string) => void;
  isLoading: boolean;
}

export default function ServiceGrid({ onSelect, isLoading }: ServiceGridProps) {
  return (
    <div className="service-grid">
      <p className="service-grid-label">Or try a popular service</p>
      <div className="service-grid-cards">
        {SERVICE_PRESETS.map((svc) => (
          <ServiceCard
            key={svc.name}
            name={svc.name}
            icon={svc.icon}
            color={svc.color}
            onClick={onSelect}
            isLoading={isLoading}
          />
        ))}
      </div>
    </div>
  );
}
