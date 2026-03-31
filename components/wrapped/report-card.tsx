'use client'

import { Grades, AllPlayRecord } from '@/lib/types'
import { SectionHeader } from '@/components/wrapped/section-header'

interface ReportCardProps {
  grades: Grades
  allPlay: AllPlayRecord
  finalPlacement?: number
}

function getGradeClass(grade: string): string {
  const base = grade.replace('+', '').replace('-', '').toLowerCase()
  switch (base) {
    case 'a': return 'grade-a'
    case 'b': return 'grade-b'
    case 'c': return 'grade-c'
    case 'd': return 'grade-d'
    case 'f': return 'grade-f'
    default: return 'text-foreground'
  }
}

function getGradeProgress(grade: string): number {
  const gradeMap: Record<string, number> = {
    'A+': 100, 'A': 95, 'A-': 90,
    'B+': 85, 'B': 80, 'B-': 75,
    'C+': 70, 'C': 65, 'C-': 60,
    'D+': 55, 'D': 50, 'D-': 45,
    'F': 30,
  }
  return gradeMap[grade] || 50
}

function getGradeDescription(category: string, grade: string, allPlay?: AllPlayRecord): string {
  const isGood = ['A+', 'A', 'A-', 'B+', 'B'].includes(grade)
  const isBad = ['D+', 'D', 'D-', 'F'].includes(grade)
  
  switch (category) {
    case 'drafting':
      if (isGood) return 'Your draft class carried you. Built different from day one.'
      if (isBad) return 'The draft board wasn\'t kind. Rebuilding starts in October.'
      return 'Some hits, some misses. A draft you can live with.'
    case 'trading':
      if (isGood) return 'You fleeced the league. Next Sam Presti in the making.'
      if (isBad) return 'The trade market ate you alive this year.'
      return 'Dealt some, got dealt some. The trade game was a wash.'
    case 'waiverWire':
      if (isGood) return 'Waiver wire assassin. You found gems nobody else saw coming.'
      if (isBad) return 'The wire was dry for you. Slim pickings all season.'
      return 'Decent pickups here and there. Nothing league-winning.'
    case 'luck':
      if (isGood) return 'The schedule smiled on you. You dodged the big guns when it counted.'
      if (isBad) return 'You caught every team on their best week. Brutal scheduling.'
      return 'No excuses either way. Your record is what you earned.'
    case 'coaching':
      if (isGood) return 'Your lineup instincts were sharp. Right starters, right matchups.'
      if (isBad) return 'Points rotted on your bench all season. Start your studs.'
      return 'Some weeks you nailed it, some weeks you didn\'t. Par for the course.'
    default:
      return ''
  }
}

function getPlacementFlavor(p: number): { label: string; description: string } {
  if (p === 1) return { label: 'Champion', description: 'Raised the trophy. The rest is just details.' }
  if (p === 2) return { label: 'Runner-Up', description: 'So close you could taste it. Next year.' }
  if (p <= 4) return { label: 'Top 4', description: 'Deep playoff run. One bounce away from the finals.' }
  if (p <= 6) return { label: 'Playoffs', description: 'Made the dance, but the music stopped early.' }
  if (p <= 8) return { label: 'Bubble', description: 'On the outside looking in. Painful place to be.' }
  if (p <= 10) return { label: 'Lottery', description: 'A season to forget. Time to hit the draft board.' }
  return { label: 'Bottom', description: 'Nowhere to go but up.' }
}

export function ReportCard({ grades, allPlay, finalPlacement }: ReportCardProps) {
  const categories = [
    { key: 'drafting', label: 'Drafting' },
    { key: 'trading', label: 'Trading' },
    { key: 'waiverWire', label: 'Waiver Wire' },
    { key: 'coaching', label: 'Coaching' },
    { key: 'luck', label: 'Luck' },
  ]

  const overallProgress = getGradeProgress(grades.overall)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      <SectionHeader
        number="11"
        title="Report Card"
        description="The verdict is in. Here's how your season stacks up."
      />

      {/* Overall Grade - Hero */}
      <div className="flex flex-col items-center justify-center py-16 mb-12 border border-gold/50 bg-gold/5">
        <p className="font-mono text-xs text-gold uppercase tracking-widest mb-4">Overall Grade</p>
        <p className={`font-mono text-[6rem] md:text-[12rem] lg:text-[16rem] font-bold leading-none ${getGradeClass(grades.overall)}`}>
          {grades.overall}
        </p>
        <div className="w-full max-w-md mt-8 px-8">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-gold rounded-full transition-all duration-1000"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Individual Grades */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {categories.map(({ key, label }) => {
          const grade = grades[key as keyof Grades]
          const progress = getGradeProgress(grade)
          const description = getGradeDescription(key, grade, key === 'luck' ? allPlay : undefined)
          
          return (
            <div key={key} className="p-6 border border-border hover:border-muted-foreground/30 transition-colors">
              <div className="flex items-start justify-between mb-4">
                <p className="font-mono text-sm text-muted-foreground uppercase tracking-widest">
                  {label}
                </p>
                <p className={`font-mono text-4xl md:text-5xl font-bold ${getGradeClass(grade)}`}>
                  {grade}
                </p>
              </div>
              
              {/* Progress Bar */}
              <div className="h-1 bg-muted rounded-full overflow-hidden mb-4">
                <div 
                  className={`h-full rounded-full transition-all duration-700 ${
                    progress >= 80 ? 'bg-win' :
                    progress >= 60 ? 'bg-gold' :
                    progress >= 40 ? 'bg-chart-3' :
                    'bg-loss'
                  }`}
                  style={{ width: `${progress}%` }}
                />
              </div>
              
              <p className="font-mono text-xs text-muted-foreground leading-relaxed">
                {description}
              </p>
            </div>
          )
        })}

        {finalPlacement && (() => {
          const { label, description } = getPlacementFlavor(finalPlacement)
          return (
            <div className="p-6 border border-gold/50 bg-gold/5">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="font-mono text-sm text-gold uppercase tracking-widest">
                    Finish
                  </p>
                  <p className="font-mono text-xs text-muted-foreground mt-1">
                    {label}
                  </p>
                </div>
                <p className="font-mono text-4xl md:text-5xl font-bold text-gold">
                  #{finalPlacement}
                </p>
              </div>
              <p className="font-mono text-xs text-muted-foreground leading-relaxed">
                {description}
              </p>
            </div>
          )
        })()}
      </div>
    </section>
  )
}
