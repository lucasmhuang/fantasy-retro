'use client'

import { useState, useCallback } from 'react'
import { useIsMobile } from './use-mobile'

export function useChartTooltip() {
  const [pos, setPos] = useState({ x: 0, y: 0 })
  const isMobile = useIsMobile()

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    if (isMobile) return
    setPos({ x: e.clientX, y: e.clientY })
  }, [isMobile])

  return { pos, onMouseMove, isMobile }
}
