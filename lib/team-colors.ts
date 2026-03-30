import type { CSSProperties } from 'react'

interface TeamColor {
  primary: string
  secondary: string
  glow: number
}

export const TEAM_COLORS: Record<number, TeamColor> = {
  8:  { primary: '#D4A017', secondary: '#1A6B4F', glow: 1.0  },
  6:  { primary: '#C75B3A', secondary: '#F5DEB3', glow: 0.8  },
  2:  { primary: '#7B2D5F', secondary: '#2D1B40', glow: 0.8  },
  11: { primary: '#1E40AF', secondary: '#93C5FD', glow: 0.8  },
  1:  { primary: '#8B1A1A', secondary: '#C9A227', glow: 0.7  },
  4:  { primary: '#FDB515', secondary: '#003262', glow: 0.7  },
  10: { primary: '#64748B', secondary: '#CBD5E1', glow: 0.55 },
  3:  { primary: '#7C3AED', secondary: '#C4B5FD', glow: 0.65 },
  12: { primary: '#B45309', secondary: '#78350F', glow: 0.55 },
  9:  { primary: '#EAB308', secondary: '#1E3A5F', glow: 0.55 },
  7:  { primary: '#06B6D4', secondary: '#164E63', glow: 0.5  },
  5:  { primary: '#A0522D', secondary: '#DC7958', glow: 0.5  },
}

const FALLBACK: TeamColor = {
  primary: '#D4A017',
  secondary: '#1A6B4F',
  glow: 0.7,
}

interface TeamEntry {
  id: number
  name: string
  manager: string
}

export function buildNameLookup(teams: TeamEntry[]): { byId: Record<number, string>; byName: Record<string, string> } {
  const byId: Record<number, string> = {}
  const byName: Record<string, string> = {}
  for (const t of teams) {
    const first = t.manager.split(' ')[0]
    byId[t.id] = first
    byName[t.name] = first
  }
  return { byId, byName }
}

export function getTeamCSSVars(teamId: number): CSSProperties {
  const colors = TEAM_COLORS[teamId] ?? FALLBACK
  return {
    '--team-primary': colors.primary,
    '--team-secondary': colors.secondary,
    '--team-glow': String(colors.glow),
  } as CSSProperties
}
