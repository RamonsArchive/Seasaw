export default function LoadingSkeleton() {
  return (
    <div className="nutrition-label skeleton-card">
      <div className="nl-header">
        <div className="nl-header-info">
          <div className="skeleton skeleton-title" />
          <div className="skeleton skeleton-subtitle" />
          <div className="skeleton skeleton-pills" />
        </div>
        <div className="skeleton skeleton-badge" />
      </div>
      <div className="nl-divider" />
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="skeleton skeleton-row" />
      ))}
    </div>
  );
}
