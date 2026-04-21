import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface CardProps {
  children: ReactNode
  className?: string
  variant?: 'default' | 'featured' | 'dark' | 'glass'
  padding?: 'sm' | 'md' | 'lg'
  hover?: boolean
}

const paddings = {
  sm: 'p-5',
  md: 'p-6 md:p-7',
  lg: 'p-7 md:p-9',
}

const variants = {
  default:
    'bg-white border border-ink-200/80 shadow-[0_1px_2px_rgb(15_23_42_/_0.04),0_4px_14px_rgb(15_23_42_/_0.06)]',
  featured:
    'bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 text-white shadow-[0_10px_20px_rgb(15_23_42_/_0.2),0_24px_48px_rgb(15_23_42_/_0.25)] ring-1 ring-brand-500/30',
  dark:
    'bg-ink-900 text-white shadow-[0_10px_20px_rgb(15_23_42_/_0.2),0_24px_48px_rgb(15_23_42_/_0.25)]',
  glass:
    'bg-white/70 backdrop-blur-xl border border-white/40 shadow-[0_10px_20px_rgb(15_23_42_/_0.1)]',
}

export function Card({
  children,
  className,
  variant = 'default',
  padding = 'md',
  hover = false,
}: CardProps) {
  return (
    <div
      className={cn(
        'rounded-2xl transition-all duration-300',
        paddings[padding],
        variants[variant],
        hover && 'hover:shadow-[0_10px_20px_rgb(15_23_42_/_0.1),0_24px_48px_rgb(15_23_42_/_0.15)] hover:-translate-y-0.5',
        className,
      )}
    >
      {children}
    </div>
  )
}
