export const AXIS_TICK = {
  fill: 'oklch(0.60 0 0)',
  fontSize: 12,
  fontFamily: 'var(--font-barlow-condensed)',
} as const

export const COLORS = {
  win: 'oklch(0.65 0.20 145)',
  loss: 'oklch(0.55 0.22 25)',
  gold: 'oklch(0.80 0.18 85)',
  muted: 'oklch(0.40 0 0)',
  dim: 'oklch(0.25 0 0)',
  foreground: 'oklch(0.98 0 0)',
  tick: 'oklch(0.60 0 0)',
  grid: 'oklch(0.25 0 0)',
} as const

export const GRADE_COLORS: Record<string, string> = {
  'A+': 'text-win', A: 'text-win', 'A-': 'text-win',
  'B+': 'text-win/70', B: 'text-win/70', 'B-': 'text-win/70',
  'C+': 'text-muted-foreground', C: 'text-muted-foreground', 'C-': 'text-muted-foreground',
  'D+': 'text-loss/70', D: 'text-loss/70', F: 'text-loss',
}
