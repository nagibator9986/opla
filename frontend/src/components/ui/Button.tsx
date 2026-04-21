import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'subtle'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  loading?: boolean
  leftIcon?: ReactNode
  rightIcon?: ReactNode
  fullWidth?: boolean
}

const base =
  'relative inline-flex items-center justify-center gap-2 font-semibold rounded-xl ' +
  'transition-all duration-200 cursor-pointer select-none whitespace-nowrap ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ' +
  'disabled:opacity-60 disabled:cursor-not-allowed disabled:pointer-events-none ' +
  'active:scale-[0.98]'

const variants: Record<NonNullable<ButtonProps['variant']>, string> = {
  primary:
    'bg-ink-900 text-white shadow-md hover:bg-ink-800 hover:shadow-lg ' +
    'focus-visible:ring-ink-900',
  secondary:
    'bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 shadow-md ' +
    'hover:from-brand-300 hover:to-brand-400 hover:shadow-lg ' +
    'focus-visible:ring-brand-500',
  outline:
    'border border-ink-200 bg-white text-ink-900 hover:bg-ink-50 hover:border-ink-300 ' +
    'focus-visible:ring-ink-900',
  ghost:
    'text-ink-700 hover:bg-ink-100 hover:text-ink-900 focus-visible:ring-ink-900',
  subtle:
    'bg-brand-100 text-brand-800 hover:bg-brand-200 focus-visible:ring-brand-500',
}

const sizes: Record<NonNullable<ButtonProps['size']>, string> = {
  sm: 'px-3.5 py-2 text-sm',
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
  xl: 'px-8 py-4 text-base',
}

const Spinner = () => (
  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
    <path
      className="opacity-75"
      fill="currentColor"
      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
    />
  </svg>
)

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        base,
        variants[variant],
        sizes[size],
        fullWidth && 'w-full',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Spinner /> : leftIcon}
      <span>{children}</span>
      {!loading && rightIcon}
    </button>
  )
}
