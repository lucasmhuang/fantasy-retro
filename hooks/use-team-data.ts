import { useEffect, useState } from 'react'
import type { TeamData, LeagueMeta } from '@/lib/types'

interface UseTeamDataResult {
  teamData: TeamData | null
  leagueMeta: LeagueMeta | null
  isLoading: boolean
  error: string | null
}

export function useTeamData(teamId: string): UseTeamDataResult {
  const [teamData, setTeamData] = useState<TeamData | null>(null)
  const [leagueMeta, setLeagueMeta] = useState<LeagueMeta | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setTeamData(null)
    setLeagueMeta(null)
    setError(null)

    Promise.all([
      fetch(`/data/team_${teamId}.json`).then((res) => {
        if (!res.ok) throw new Error(`Team not found (${res.status})`)
        return res.json()
      }),
      fetch('/data/league_meta.json').then((res) => {
        if (!res.ok) throw new Error(`Failed to load league data (${res.status})`)
        return res.json()
      }),
    ])
      .then(([team, league]) => {
        setTeamData(team)
        setLeagueMeta(league)
      })
      .catch((err: Error) => setError(err.message))
  }, [teamId])

  return { teamData, leagueMeta, isLoading: !teamData && !leagueMeta && !error, error }
}
