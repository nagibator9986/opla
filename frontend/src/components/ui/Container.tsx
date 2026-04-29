import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface ContainerProps {
  children: ReactNode
  className?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const sizes = {
  sm: 'max-w-3xl',
  md: 'max-w-5xl',
  lg: 'max-w-6xl',
  xl: 'max-w-7xl',
}

export function Container({ children, className, size = 'lg' }: ContainerProps) {
  return (
    <div className={cn('mx-auto w-full px-4 sm:px-6 lg:px-8', sizes[size], className)}>
      {children}
    </div>
  )
}

export function Section({
  id,
  children,
  className,
  background = 'white',
  decor = false,
}: {
  id?: string
  children: ReactNode
  className?: string
  background?: 'white' | 'ink-50' | 'ink-900' | 'gradient'
  /**
   * Подкладывает декоративный руническо-circuit фон-слой и мягкое
   * brand-свечение — повторяет тематику шапки лендинга в светлой
   * минималистичной трактовке. Имеет смысл только на светлых фонах
   * (white, ink-50, gradient).
   */
  decor?: boolean
}) {
  const bgClass = {
    white: 'bg-white',
    'ink-50': 'bg-ink-50',
    'ink-900': 'bg-ink-900 text-white',
    gradient: 'bg-gradient-to-b from-white via-ink-50 to-white',
  }[background]

  return (
    <section
      id={id}
      className={cn(
        'relative py-16 md:py-24 lg:py-28 scroll-mt-20 overflow-hidden',
        bgClass,
        className,
      )}
    >
      {decor && (
        <>
          {/* Рунически-схематический паттерн с feathered-краями */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-runes-light bg-runes-fade-mask"
          />
          {/* Очень мягкий brand-glow в верхней части — связывает секцию
              с шапкой лендинга визуально */}
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-[radial-gradient(ellipse_at_top,rgb(245_158_11_/_0.08),transparent_70%)]"
          />
        </>
      )}
      <div className="relative">{children}</div>
    </section>
  )
}
