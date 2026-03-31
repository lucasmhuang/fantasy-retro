import { useEffect, useState } from 'react'
import type { LeagueMeta } from '@/lib/types'

interface UseLeagueDataResult {
  data: LeagueMeta | null
  isLoading: boolean
  error: string | null
}

export function useLeagueData(): UseLeagueDataResult {
  const [data, setData] = useState<LeagueMeta | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/data/league_meta.json')
      .then((res) => {
        if (!res.ok) throw new Error(`Failed to load league data (${res.status})`)
        return res.json()
      })
      .then(setData)
      .catch((err: Error) => setError(err.message))
  }, [])

  return { data, isLoading: !data && !error, error }
}
