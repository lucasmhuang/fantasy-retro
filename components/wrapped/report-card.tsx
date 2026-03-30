'use client'

import { Grades, AllPlayRecord } from '@/lib/types'
import { ParallaxNumber } from '@/components/ui/parallax-number'

interface ReportCardProps {
  grades: Grades
  allPlay: AllPlayRecord
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
      if (isGood) return 'Strong draft picks formed your foundation.'
      if (isBad) return 'Draft picks underperformed expectations.'
      return 'Solid draft with room for improvement.'
    case 'trading':
      if (isGood) return 'Excellent trade decisions boosted your roster.'
      if (isBad) return 'Trades hurt more than they helped.'
      return 'Trades were a mixed bag overall.'
    case 'waiverWire':
      if (isGood) return 'Great pickups from the wire added depth.'
      if (isBad) return 'Missed opportunities on the waiver wire.'
      return 'Average waiver wire activity.'
    case 'luck':
      if (isGood) return 'The schedule gods favored you this season.'
      if (isBad) return 'The schedule gods were not kind to you.'
      return 'Luck was neither here nor there.'
    case 'consistency':
      if (isGood) return 'Reliable weekly scoring kept you competitive.'
      if (isBad) return 'Boom-or-bust performances hurt your record.'
      return 'Some good weeks, some bad weeks.'
    default:
      return ''
  }
}

export function ReportCard({ grades, allPlay }: ReportCardProps) {
  const categories = [
    { key: 'drafting', label: 'Drafting' },
    { key: 'trading', label: 'Trading' },
    { key: 'waiverWire', label: 'Waiver Wire' },
    { key: 'luck', label: 'Luck' },
    { key: 'consistency', label: 'Consistency' },
  ]

  const overallProgress = getGradeProgress(grades.overall)

  return (
    <section className="relative min-h-screen px-6 py-24 md:px-12 lg:px-24">
      {/* Section Header */}
      <div className="mb-16">
        <ParallaxNumber gradient className="font-mono text-6xl md:text-8xl font-bold text-muted-foreground/10">
          11
        </ParallaxNumber>
        <h2 className="font-mono text-3xl md:text-4xl font-bold tracking-tight text-foreground uppercase -mt-8 md:-mt-12">
          Report Card
        </h2>
        <p className="font-mono text-base text-muted-foreground mt-2">
          Your final season grades across all categories.
        </p>
      </div>

      {/* Overall Grade - Hero */}
      <div className="flex flex-col items-center justify-center py-16 mb-12 border border-gold/50 bg-gold/5">
        <p className="font-mono text-xs text-gold uppercase tracking-widest mb-4">Overall Grade</p>
        <p className={`font-mono text-[12rem] md:text-[16rem] font-bold leading-none ${getGradeClass(grades.overall)}`}>
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
      </div>
    </section>
  )
}
