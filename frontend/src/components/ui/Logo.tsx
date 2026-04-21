import { cn } from '../../lib/cn'

interface LogoProps {
  className?: string
  variant?: 'dark' | 'light'
  showWordmark?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const MARK_SIZE = {
  sm: 'w-8 h-8',
  md: 'w-9 h-9',
  lg: 'w-11 h-11',
} as const

const ICON_SIZE = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
} as const

const TEXT_SIZE = {
  sm: 'text-base',
  md: 'text-lg',
  lg: 'text-xl',
} as const

export function Logo({
  className,
  variant = 'dark',
  showWordmark = true,
  size = 'md',
}: LogoProps) {
  const textColor = variant === 'dark' ? 'text-ink-900' : 'text-white'
  return (
    <div className={cn('inline-flex items-center gap-2.5', className)}>
      <span
        className={cn(
          'relative inline-flex items-center justify-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 shadow-md ring-1 ring-brand-600/20',
          MARK_SIZE[size],
        )}
      >
        <svg viewBox="0 0 24 24" className={cn('text-white', ICON_SIZE[size])} fill="none">
          <path
            d="M4 17V7c0-1.1.9-2 2-2h12c1.1 0 2 .9 2 2v10c0 1.1-.9 2-2 2H6c-1.1 0-2-.9-2-2z"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinejoin="round"
          />
          <path d="M7 10l3 3 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      {showWordmark && (
        <span className={cn('font-bold tracking-tight', TEXT_SIZE[size], textColor)}>
          Baqsy<span className="text-brand-500">.</span>
        </span>
      )}
    </div>
  )
}
