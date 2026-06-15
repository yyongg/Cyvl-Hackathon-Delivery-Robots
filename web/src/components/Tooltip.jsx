import { TIER_COLORS } from '../constants'
import { getScoreColor } from '../utils/colors'

// Floating tooltip that follows the cursor while hovering a segment.
export default function Tooltip({ tooltip }) {
  const { x, y, props } = tooltip
  return (
    <div className="tooltip" style={{ left: x + 14, top: y - 72 }}>
      <div className="tooltip-score" style={{ color: getScoreColor(props.composite_score) }}>
        {props.composite_score?.toFixed(1) ?? '—'}
      </div>
      <div className="tooltip-label">{props.label ?? '—'}</div>
      <div className="tooltip-tier" style={{ background: TIER_COLORS[props.tier] }}>
        {(props.tier ?? '—').toUpperCase()}
      </div>
    </div>
  )
}
