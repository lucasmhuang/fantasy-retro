'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useIsMobile } from '@/hooks/use-mobile'

interface AmbientHaloProps {
  sectionCount?: number
  color?: string
}

export function AmbientHalo({ sectionCount = 12, color }: AmbientHaloProps) {
  const isMobile = useIsMobile()
  const c = color ?? 'var(--team-primary)'

  if (isMobile) {
    return (
      <div
        className="fixed inset-0 z-0 pointer-events-none"
        style={{
          background: `radial-gradient(ellipse at 50% 50%, ${c} 0%, transparent 70%)`,
          opacity: 0.04,
        }}
        aria-hidden="true"
      />
    )
  }

  return <AmbientHaloAnimated sectionCount={sectionCount} color={c} />
}

function AmbientHaloAnimated({ sectionCount, color }: { sectionCount: number; color: string }) {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll()

  const centerY = useTransform(scrollYProgress, [0, 1], [30, 70])

  const breathe = useTransform(scrollYProgress, (p) => {
    const sectionProgress = p * sectionCount
    const withinSection = sectionProgress % 1
    const triangle = 1 - Math.abs(withinSection - 0.5) * 2
    return 0.03 + triangle * 0.03
  })

  const background = useTransform(
    centerY,
    (y) => `radial-gradient(ellipse at 50% ${y}%, ${color} 0%, transparent 70%)`
  )

  return (
    <motion.div
      ref={ref}
      className="fixed inset-0 z-0 pointer-events-none"
      style={{ background, opacity: breathe }}
      aria-hidden="true"
    />
  )
}
