'use client'

import React, { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useScrollReveal } from '@/hooks/use-scroll-reveal'

interface ScrollRevealProps {
  children: React.ReactNode
  className?: string
  direction?: 'up' | 'down' | 'left' | 'right'
  distance?: number
  delay?: number
  duration?: number
  threshold?: number
  stagger?: number
  exitEffect?: boolean
}

const directionTransform = {
  up: (d: number) => `translateY(${d}px)`,
  down: (d: number) => `translateY(-${d}px)`,
  left: (d: number) => `translateX(${d}px)`,
  right: (d: number) => `translateX(-${d}px)`,
}

export function ScrollReveal({
  children,
  className = '',
  direction = 'up',
  distance = 30,
  delay = 0,
  duration = 700,
  threshold = 0.15,
  stagger = 0,
  exitEffect = true,
}: ScrollRevealProps) {
  const { ref: ioRef, isVisible } = useScrollReveal({ threshold })
  const scrollRef = useRef(null)

  const { scrollYProgress } = useScroll({
    target: scrollRef,
    offset: ['start start', 'end start'],
  })

  const exitScale = useTransform(scrollYProgress, [0, 0.4], [1, 0.97])
  const exitOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])

  const entryStyle = {
    opacity: isVisible ? 1 : 0,
    transform: isVisible ? 'none' : directionTransform[direction](distance),
    transition: `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
    transitionDelay: isVisible ? `${delay}ms` : '0ms',
    willChange: 'opacity, transform' as const,
  }

  if (stagger > 0) {
    const items = React.Children.toArray(children)
    return (
      <div ref={(el) => { (ioRef as React.MutableRefObject<HTMLDivElement | null>).current = el; (scrollRef as React.MutableRefObject<HTMLDivElement | null>).current = el }} className={className} style={{ position: 'relative' }}>
        <motion.div style={exitEffect ? { scale: exitScale, opacity: exitOpacity } : undefined}>
          {items.map((child, i) => (
            <div
              key={i}
              style={{
                opacity: isVisible ? 1 : 0,
                transform: isVisible ? 'none' : directionTransform[direction](distance),
                transition: `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
                transitionDelay: isVisible ? `${delay + i * stagger}ms` : '0ms',
                willChange: 'opacity, transform',
              }}
            >
              {child}
            </div>
          ))}
        </motion.div>
      </div>
    )
  }

  return (
    <div
      ref={(el) => { (ioRef as React.MutableRefObject<HTMLDivElement | null>).current = el; (scrollRef as React.MutableRefObject<HTMLDivElement | null>).current = el }}
      className={className}
      style={{ position: 'relative' }}
    >
      <motion.div style={exitEffect ? { scale: exitScale, opacity: exitOpacity, ...entryStyle } : entryStyle}>
        {children}
      </motion.div>
    </div>
  )
}
