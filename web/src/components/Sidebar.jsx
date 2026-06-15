import { TIER_COLORS, TIER_LABELS, TIER_RANGES, TIER_ORDER } from '../constants'

// Left-hand control panel: summary stats, tier filters, and the score legend.
export default function Sidebar({ loading, stats, activeTiers, onToggleTier }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Delivery Robot</div>
        <div className="sidebar-subtitle">Feasibility Map</div>
        <div className="sidebar-location">Somerville, MA</div>
      </div>

      {loading ? (
        <div className="loading-msg">Loading segments…</div>
      ) : stats ? (
        <>
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-value">{stats.total.toLocaleString()}</span>
              <span className="stat-label">Segments</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{stats.avgScore}</span>
              <span className="stat-label">Avg Score</span>
            </div>
          </div>

          <div className="tier-section">
            <div className="section-title">Feasibility Tiers</div>
            {TIER_ORDER.map(tier => {
              const count = stats[tier]
              const pct = ((count / stats.total) * 100).toFixed(0)
              const active = activeTiers.has(tier)
              return (
                <button
                  key={tier}
                  className={`tier-btn ${active ? 'tier-btn--active' : 'tier-btn--dim'}`}
                  onClick={() => onToggleTier(tier)}
                >
                  <span className="tier-dot" style={{ background: TIER_COLORS[tier] }} />
                  <span className="tier-info">
                    <span className="tier-name">{TIER_LABELS[tier]}</span>
                    <span className="tier-range">{TIER_RANGES[tier]}</span>
                  </span>
                  <span className="tier-count">
                    <strong>{count.toLocaleString()}</strong>
                    <span className="tier-pct">{pct}%</span>
                  </span>
                  <div
                    className="tier-bar"
                    style={{
                      width: `${pct}%`,
                      background: TIER_COLORS[tier],
                      opacity: active ? 0.25 : 0.1,
                    }}
                  />
                </button>
              )
            })}
          </div>

          <div className="gradient-section">
            <div className="section-title">Score Gradient</div>
            <div className="gradient-bar" />
            <div className="gradient-labels">
              <span>0</span>
              <span>40</span>
              <span>70</span>
              <span>100</span>
            </div>
          </div>
        </>
      ) : null}

      <div className="sidebar-footer">
        <div>Data: Cyvl Hackathon S3</div>
        <div>Click a segment to inspect</div>
      </div>
    </aside>
  )
}
