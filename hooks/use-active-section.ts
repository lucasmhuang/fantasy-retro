import { useEffect, useState } from 'react'

export function useActiveSection(selector = '[data-section]'): number {
  const [active, setActive] = useState(0)

  useEffect(() => {
    const sections = document.querySelectorAll(selector)
    if (sections.length === 0) return

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            const index = Array.from(sections).indexOf(entry.target)
            if (index !== -1) setActive(index)
          }
        }
      },
      { rootMargin: '0px 0px -60% 0px' },
    )

    for (const section of sections) observer.observe(section)
    return () => observer.disconnect()
  }, [selector])

  return active
}
