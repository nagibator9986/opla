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
}: {
  id?: string
  children: ReactNode
  className?: string
  background?: 'white' | 'ink-50' | 'ink-900' | 'gradient'
}) {
  const bgClass = {
    white: 'bg-white',
    'ink-50': 'bg-ink-50',
    'ink-900': 'bg-ink-900 text-white',
    gradient: 'bg-gradient-to-b from-white via-ink-50 to-white',
  }[background]

  return (
    <section id={id} className={cn('py-16 md:py-24 lg:py-28 scroll-mt-20', bgClass, className)}>
      {children}
    </section>
  )
}
