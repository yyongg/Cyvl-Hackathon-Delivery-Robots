import { TIER_COLORS, SCORE_FIELDS } from '../constants'
import { getScoreColor } from '../utils/colors'
import ScoreBar from './ScoreBar'

// Slide-in panel showing the full score breakdown for a selected segment.
export default function DetailPanel({ feature, onClose }) {
  const p = feature
  return (
    <div className="detail-panel">
      <div className="detail-header">
        <div>
          <div className="detail-title">Segment Details</div>
          <code className="detail-id">{p.id ? p.id.slice(0, 16) + '…' : '—'}</code>
        </div>
        <button className="close-btn" onClick={onClose} aria-label="Close">×</button>
      </div>

      <div className="composite-block">
        <div className="composite-score" style={{ color: getScoreColor(p.composite_score) }}>
          {p.composite_score != null ? p.composite_score.toFixed(1) : '—'}
        </div>
        <div className="composite-meta">
          <span
            className="tier-badge"
            style={{ background: TIER_COLORS[p.tier] ?? '#94a3b8' }}
          >
            {(p.tier ?? '—').toUpperCase()}
          </span>
          <span className="condition-label">{p.label ?? '—'}</span>
        </div>
      </div>

      <section className="detail-section">
        <h4>Score Breakdown</h4>
        {SCORE_FIELDS.map(({ key, label, weight }) => (
          <div key={key} className="score-row">
            <div className="score-row-header">
              <span className="score-row-label">{label}</span>
              <span className="score-row-weight">{weight}</span>
            </div>
            <ScoreBar value={p[key]} />
          </div>
        ))}
      </section>

      <section className="detail-section">
        <h4>Raw Measurements</h4>
        <div className="metric-grid">
          {[
            { label: 'Width', value: p.width_m != null ? `${p.width_m} m` : '—' },
            { label: 'Slope', value: p.slope_pct != null ? `${p.slope_pct}%` : '—' },
            { label: 'Curb Ramps', value: p.curb_ramp_count ?? '—' },
            { label: 'Obstructions', value: p.obstruction_count ?? '—' },
            { label: '311 Complaints', value: p.complaint_count ?? '—' },
            { label: 'PCI Score', value: p.pavement_score != null ? p.pavement_score.toFixed(1) : '—' },
          ].map(({ label, value }) => (
            <div key={label} className="metric-item">
              <span className="metric-label">{label}</span>
              <span className="metric-value">{value}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
