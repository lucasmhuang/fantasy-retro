import type { ReactNode } from 'react'
import { ParallaxNumber } from '@/components/ui/parallax-number'

interface SectionHeaderProps {
  number: string
  title: string
  description?: ReactNode
}

export function SectionHeader({ number: num, title, description }: SectionHeaderProps) {
  return (
    <div className="mb-16">
      <ParallaxNumber gradient className="font-mono text-4xl md:text-6xl lg:text-8xl font-bold text-muted-foreground/10">
        {num}
      </ParallaxNumber>
      <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
        {title}
      </h2>
      {description && (
        <p className="font-mono text-base text-muted-foreground mt-2">
          {description}
        </p>
      )}
    </div>
  )
}
