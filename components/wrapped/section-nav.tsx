'use client'

import { useLenis } from '@/components/providers/smooth-scroll-provider'

interface Section {
  id: string
  label: string
}

interface SectionNavProps {
  sections: Section[]
  activeSection: number
}

export function SectionNav({ sections, activeSection }: SectionNavProps) {
  const lenis = useLenis()

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id)
    if (!element) return
    if (lenis) {
      lenis.scrollTo(element, { duration: 1.5 })
    } else {
      element.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <nav className="fixed right-6 top-1/2 -translate-y-1/2 z-50 hidden lg:flex flex-col items-end gap-2">
      {sections.map((section, index) => {
        const isActive = activeSection === index
        return (
          <button
            key={section.id}
            onClick={() => scrollToSection(section.id)}
            className={`font-mono text-[10px] tracking-widest uppercase transition-all duration-300 ${
              isActive
                ? 'text-gold translate-x-0'
                : 'text-muted-foreground/40 hover:text-muted-foreground translate-x-2'
            }`}
          >
            {section.label}
          </button>
        )
      })}
    </nav>
  )
}
