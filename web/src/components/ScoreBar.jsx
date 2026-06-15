import { getScoreColor } from '../utils/colors'

// Horizontal progress bar for a single 0–100 sub-score.
export default function ScoreBar({ value }) {
  const v = value ?? 0
  return (
    <div className="score-bar-wrap">
      <div className="score-bar-track">
        <div className="score-bar-fill" style={{ width: `${v}%`, background: getScoreColor(v) }} />
      </div>
      <span className="score-bar-value">{v.toFixed(0)}</span>
    </div>
  )
}
