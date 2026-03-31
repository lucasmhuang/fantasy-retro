'use client'

import { useCountUp } from '@/hooks/use-count-up'

interface CountUpProps {
  value: number
  decimals?: number
  prefix?: string
}

export function CountUp({ value, decimals = 0, prefix = '' }: CountUpProps) {
  const { ref, displayValue } = useCountUp(value, { decimals })
  return <span ref={ref}>{prefix}{displayValue}</span>
}
