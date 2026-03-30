'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useIsMobile } from '@/hooks/use-mobile'

interface ParallaxNumberProps {
  children: React.ReactNode
  className?: string
  speed?: number
  gradient?: boolean
}

export function ParallaxNumber({ children, className = '', speed = 0.3, gradient = false }: ParallaxNumberProps) {
  const isMobile = useIsMobile()
  const gradientClass = gradient ? 'text-gradient-team opacity-20' : ''

  if (isMobile) {
    return (
      <span
        style={{ display: 'block', position: 'relative' }}
        className={`${className} ${gradientClass}`}
      >
        {children}
      </span>
    )
  }

  return <ParallaxNumberAnimated className={className} speed={speed} gradientClass={gradientClass}>{children}</ParallaxNumberAnimated>
}

function ParallaxNumberAnimated({ children, className, speed, gradientClass }: { children: React.ReactNode; className: string; speed: number; gradientClass: string }) {
  const ref = useRef(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start end', 'end start'],
  })

  const y = useTransform(scrollYProgress, [0, 1], [40 * speed, -60 * speed])

  return (
    <motion.span
      ref={ref}
      style={{ y, display: 'block', position: 'relative' }}
      className={`${className} ${gradientClass}`}
    >
      {children}
    </motion.span>
  )
}
