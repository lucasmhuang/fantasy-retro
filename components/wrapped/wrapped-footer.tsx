'use client'

import Link from 'next/link'
import { League } from '@/lib/types'
import { ArrowLeft } from 'lucide-react'

interface WrappedFooterProps {
  league: League
}

export function WrappedFooter({ league }: WrappedFooterProps) {
  return (
    <footer className="relative px-6 py-24 md:px-12 lg:px-24 border-t border-border/30">
      <div className="max-w-4xl mx-auto text-center">
        {/* Logo */}
        <p className="font-mono text-4xl md:text-6xl font-bold tracking-tighter text-foreground uppercase mb-4">
          Fantasy
          <span className="text-gold"> Wrapped</span>
        </p>
        
        <p className="font-mono text-lg text-muted-foreground mb-8">
          {league.name} &mdash; {league.season}
        </p>

        {/* Back to Teams */}
        <Link 
          href="/"
          className="inline-flex items-center gap-3 px-6 py-3 border border-border hover:border-gold hover:text-gold font-mono text-sm uppercase tracking-widest transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          View All Teams
        </Link>
      </div>
    </footer>
  )
}
