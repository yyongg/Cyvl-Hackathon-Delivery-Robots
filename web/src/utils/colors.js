// Maps a 0–100 score to the tier color used throughout the UI.
export function getScoreColor(score) {
  if (score == null) return '#94a3b8'
  if (score >= 70) return '#22c55e'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}
