'use client'

import { useLayoutEffect, useRef } from 'react'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

interface UseScrollBatchOptions {
  childSelector?: string
  stagger?: number
  from?: gsap.TweenVars
  to?: gsap.TweenVars
  once?: boolean
  enabled?: boolean
  key?: number
}

export function useScrollBatch(options: UseScrollBatchOptions = {}) {
  const {
    childSelector = '[data-batch-item]',
    stagger = 0.08,
    from = { opacity: 0, y: 30 },
    to = { opacity: 1, y: 0, duration: 0.6, ease: 'power2.out' },
    once = true,
    enabled = true,
    key = 0,
  } = options
  const ref = useRef<HTMLDivElement>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  useLayoutEffect(() => {
    const el = ref.current
    if (!el || !enabled) return

    const children = el.querySelectorAll(childSelector)
    if (children.length === 0) return

    gsap.set(children, from)

    const triggers = ScrollTrigger.batch(children, {
      onEnter: (batch) => {
        gsap.to(batch, { ...to, stagger })
      },
      onEnterBack: once
        ? undefined
        : (batch) => {
            gsap.to(batch, { ...to, stagger })
          },
      onLeave: once
        ? undefined
        : (batch) => {
            gsap.set(batch, from)
          },
      onLeaveBack: once
        ? undefined
        : (batch) => {
            gsap.set(batch, from)
          },
      start: 'top 85%',
    })

    const cleanup = () => {
      if (Array.isArray(triggers)) {
        triggers.forEach((t) => t.kill())
      }
      gsap.set(children, { clearProps: 'all' })
    }

    cleanupRef.current = cleanup

    return cleanup
  }, [childSelector, stagger, once, enabled, key])

  return { ref, kill: () => cleanupRef.current?.() }
}
