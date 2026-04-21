import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface BadgeProps {
  children: ReactNode
  variant?: 'brand' | 'neutral' | 'success' | 'warning' | 'dark'
  size?: 'sm' | 'md'
  className?: string
  icon?: ReactNode
}

const variants = {
  brand: 'bg-brand-100 text-brand-800 ring-1 ring-inset ring-brand-200',
  neutral: 'bg-ink-100 text-ink-700 ring-1 ring-inset ring-ink-200',
  success: 'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  warning: 'bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200',
  dark: 'bg-ink-900/90 text-white ring-1 ring-inset ring-white/10',
}

const sizes = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-xs px-2.5 py-1',
}

export function Badge({ children, variant = 'brand', size = 'md', className, icon }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-semibold whitespace-nowrap',
        variants[variant],
        sizes[size],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  )
}
