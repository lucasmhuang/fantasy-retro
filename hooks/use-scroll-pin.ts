'use client'

import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface UseScrollPinOptions {
  endOffset?: string
  scrub?: boolean | number
  onProgress?: (progress: number) => void
}

export function useScrollPin(options: UseScrollPinOptions = {}) {
  const { endOffset = '+=100%', scrub = true, onProgress } = options
  const ref = useRef<HTMLDivElement>(null)
  const progressRef = useRef(onProgress)
  progressRef.current = onProgress

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const trigger = ScrollTrigger.create({
      trigger: el,
      start: 'top top',
      end: endOffset,
      pin: true,
      pinType: 'transform',
      anticipatePin: 1,
      scrub: scrub,
      onUpdate: (self) => {
        progressRef.current?.(self.progress)
      },
    })

    return () => {
      trigger.kill()
    }
  }, [endOffset, scrub])

  return { ref }
}
