'use client'

import { useEffect, useRef, useState } from 'react'

interface UseCountUpOptions {
  duration?: number
  decimals?: number
}

export function useCountUp(target: number, options: UseCountUpOptions = {}) {
  const { duration = 1500, decimals = 1 } = options
  const ref = useRef<HTMLElement>(null)
  const [displayValue, setDisplayValue] = useState('0')
  const hasAnimated = useRef(false)
  const frameRef = useRef<number>(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting || hasAnimated.current) return
        hasAnimated.current = true
        observer.disconnect()

        let startTime: number

        const animate = (timestamp: number) => {
          if (!startTime) startTime = timestamp
          const progress = Math.min((timestamp - startTime) / duration, 1)
          const eased = 1 - Math.pow(1 - progress, 3)
          setDisplayValue((target * eased).toFixed(decimals))
          if (progress < 1) {
            frameRef.current = requestAnimationFrame(animate)
          }
        }

        frameRef.current = requestAnimationFrame(animate)
      },
      { threshold: 0.3 }
    )

    observer.observe(el)
    return () => {
      observer.disconnect()
      cancelAnimationFrame(frameRef.current)
    }
  }, [target, duration, decimals])

  return { ref, displayValue }
}
