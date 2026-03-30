'use client'

interface MarqueeProps {
  children: React.ReactNode
  className?: string
  speed?: number
  direction?: 'left' | 'right'
  pauseOnHover?: boolean
}

export function Marquee({
  children,
  className = '',
  speed = 30,
  direction = 'left',
  pauseOnHover = false,
}: MarqueeProps) {
  const animationDirection = direction === 'left' ? 'normal' : 'reverse'

  return (
    <div
      className={`overflow-hidden ${className}`}
      style={{ maskImage: 'linear-gradient(to right, transparent, black 10%, black 90%, transparent)' }}
    >
      <div
        className={`flex w-max ${pauseOnHover ? 'hover:[animation-play-state:paused]' : ''}`}
        style={{
          animation: `marquee-scroll ${speed}s linear infinite`,
          animationDirection,
        }}
      >
        <div className="flex shrink-0">{children}</div>
        <div className="flex shrink-0" aria-hidden="true">{children}</div>
        <div className="flex shrink-0" aria-hidden="true">{children}</div>
        <div className="flex shrink-0" aria-hidden="true">{children}</div>
      </div>
    </div>
  )
}
