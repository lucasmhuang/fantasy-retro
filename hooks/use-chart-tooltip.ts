'use client'

import { useState, useCallback } from 'react'

interface TooltipPosition {
  x: number
  y: number
}

export function useChartTooltip() {
  const [pos, setPos] = useState<TooltipPosition>({ x: 0, y: 0 })

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    setPos({ x: e.clientX, y: e.clientY })
  }, [])

  return { pos, onMouseMove }
}
