'use client'

import React, { useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useScrollReveal } from '@/hooks/use-scroll-reveal'

type Variant = 'fade' | 'clip' | 'blur' | 'scale'
type ExitVariant = 'fade' | 'slide' | 'blur'

interface ScrollRevealProps {
  children: React.ReactNode
  className?: string
  variant?: Variant
  exitVariant?: ExitVariant
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

const clipHidden: Record<string, string> = {
  up: 'inset(100% 0 0 0)',
  down: 'inset(0 0 100% 0)',
  left: 'inset(0 0 0 100%)',
  right: 'inset(0 100% 0 0)',
}

function getVariantStyle(
  variant: Variant,
  direction: 'up' | 'down' | 'left' | 'right',
  distance: number,
  isVisible: boolean,
  duration: number,
  delay: number,
): React.CSSProperties {
  switch (variant) {
    case 'clip':
      return {
        clipPath: isVisible ? 'inset(0)' : clipHidden[direction],
        opacity: isVisible ? 1 : 0,
        transition: `clip-path ${duration}ms cubic-bezier(0.16, 1, 0.3, 1), opacity ${duration * 0.4}ms ease-out`,
        transitionDelay: isVisible ? `${delay}ms` : '0ms',
        willChange: 'clip-path, opacity',
      }
    case 'blur':
      return {
        filter: isVisible ? 'blur(0px)' : 'blur(8px)',
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'none' : directionTransform[direction](distance),
        transition: `filter ${duration}ms ease-out, opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
        transitionDelay: isVisible ? `${delay}ms` : '0ms',
        willChange: 'filter, opacity, transform',
      }
    case 'scale':
      return {
        transform: isVisible ? 'scale(1)' : 'scale(0.85)',
        opacity: isVisible ? 1 : 0,
        transformOrigin: 'center bottom',
        transition: `transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1), opacity ${duration * 0.6}ms ease-out`,
        transitionDelay: isVisible ? `${delay}ms` : '0ms',
        willChange: 'transform, opacity',
      }
    case 'fade':
    default:
      return {
        opacity: isVisible ? 1 : 0,
        transform: isVisible ? 'none' : directionTransform[direction](distance),
        transition: `opacity ${duration}ms ease-out, transform ${duration}ms ease-out`,
        transitionDelay: isVisible ? `${delay}ms` : '0ms',
        willChange: 'opacity, transform',
      }
  }
}

export function ScrollReveal({
  children,
  className = '',
  variant = 'fade',
  exitVariant = 'fade',
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

  const exitScale = useTransform(scrollYProgress, [0, 0.4], [1, exitVariant === 'slide' ? 1 : 0.97])
  const exitOpacity = useTransform(scrollYProgress, [0, 0.5], [1, 0])
  const exitY = useTransform(scrollYProgress, [0, 0.5], [0, exitVariant === 'slide' ? -40 : 0])

  const entryStyle = getVariantStyle(variant, direction, distance, isVisible, duration, delay)

  if (stagger > 0) {
    const items = React.Children.toArray(children)
    return (
      <div ref={(el) => { (ioRef as React.MutableRefObject<HTMLDivElement | null>).current = el; (scrollRef as React.MutableRefObject<HTMLDivElement | null>).current = el }} className={className} style={{ position: 'relative' }}>
        <motion.div style={exitEffect ? { scale: exitScale, opacity: exitOpacity, y: exitY } : undefined}>
          {items.map((child, i) => (
            <div
              key={i}
              style={getVariantStyle(variant, direction, distance, isVisible, duration, delay + i * stagger)}
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
      <motion.div style={exitEffect ? { scale: exitScale, opacity: exitOpacity, y: exitY, ...entryStyle } : entryStyle}>
        {children}
      </motion.div>
    </div>
  )
}
