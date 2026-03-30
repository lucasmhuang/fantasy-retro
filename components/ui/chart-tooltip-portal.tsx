'use client'

import { createPortal } from 'react-dom'

interface ChartTooltipPortalProps {
  active?: boolean
  pos: { x: number; y: number }
  children: React.ReactNode
  isMobile?: boolean
}

export function ChartTooltipPortal({ active, pos, children, isMobile }: ChartTooltipPortalProps) {
  if (!active || typeof document === 'undefined') return null

  if (isMobile) {
    return (
      <div className="bg-card border border-border px-4 py-3 shadow-xl">
        {children}
      </div>
    )
  }

  return createPortal(
    <div
      className="fixed z-50 pointer-events-none bg-card border border-border px-4 py-3 shadow-xl"
      style={{ left: pos.x + 14, top: pos.y - 14 }}
    >
      {children}
    </div>,
    document.body,
  )
}
