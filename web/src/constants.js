// Feasibility-tier presentation constants, shared across components.

export const TIER_COLORS = { green: '#22c55e', yellow: '#f59e0b', red: '#ef4444' }
export const TIER_LABELS = { green: 'Robot-Ready', yellow: 'Marginal', red: 'Infeasible' }
export const TIER_RANGES = { green: '≥ 70', yellow: '40–70', red: '< 40' }

// Score components shown in the detail panel, with their pipeline weights.
export const SCORE_FIELDS = [
  { key: 'score_pavement', label: 'Pavement', weight: '30%' },
  { key: 'score_width', label: 'Width', weight: '25%' },
  { key: 'score_slope', label: 'Slope', weight: '15%' },
  { key: 'score_curb_ramp', label: 'Curb Ramp', weight: '15%' },
  { key: 'score_obstructions', label: 'Obstructions', weight: '10%' },
  { key: 'score_complaints', label: '311 Complaints', weight: '5%' },
]

// Order of tiers as rendered in the sidebar.
export const TIER_ORDER = ['green', 'yellow', 'red']
