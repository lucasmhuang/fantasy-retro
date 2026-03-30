'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'

interface AmbientHaloProps {
  sectionCount?: number
  color?: string
}

export function AmbientHalo({ sectionCount = 12, color }: AmbientHaloProps) {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll()

  const centerY = useTransform(scrollYProgress, [0, 1], [30, 70])

  const breathe = useTransform(scrollYProgress, (p) => {
    const sectionProgress = p * sectionCount
    const withinSection = sectionProgress % 1
    const triangle = 1 - Math.abs(withinSection - 0.5) * 2
    return 0.03 + triangle * 0.03
  })

  const c = color ?? 'var(--team-primary)'
  const background = useTransform(
    centerY,
    (y) => `radial-gradient(ellipse at 50% ${y}%, ${c} 0%, transparent 70%)`
  )

  return (
    <motion.div
      ref={ref}
      className="fixed inset-0 z-0 pointer-events-none"
      style={{
        background,
        opacity: breathe,
      }}
      aria-hidden="true"
    />
  )
}
