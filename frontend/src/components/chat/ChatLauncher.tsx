import { useState } from 'react'
import { ChatWidget } from './ChatWidget'
import { cn } from '../../lib/cn'

interface ChatLauncherProps {
  label?: string
  variant?: 'primary' | 'secondary' | 'floating'
  className?: string
  size?: 'md' | 'lg' | 'xl'
  children?: React.ReactNode
}

const base =
  'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 ' +
  'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 ' +
  'active:scale-[0.98] cursor-pointer select-none'

const variants = {
  primary: 'bg-ink-900 text-white shadow-md hover:bg-ink-800 hover:shadow-lg focus-visible:ring-ink-900',
  secondary:
    'bg-gradient-to-b from-brand-400 to-brand-500 text-ink-950 shadow-md ' +
    'hover:from-brand-300 hover:to-brand-400 hover:shadow-lg focus-visible:ring-brand-500',
  floating:
    'bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-2xl ' +
    'hover:shadow-[0_20px_40px_rgb(245_158_11_/_0.4)] ring-4 ring-white',
}

const sizes = {
  md: 'px-5 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
  xl: 'px-7 py-4 text-base',
}

export function ChatLauncher({
  label,
  variant = 'primary',
  className,
  size = 'lg',
  children,
}: ChatLauncherProps) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className={cn(base, variants[variant], sizes[size], className)}
      >
        {children ?? (
          <>
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path
                d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            {label ?? 'Начать чат'}
          </>
        )}
      </button>
      <ChatWidget open={open} onClose={() => setOpen(false)} />
    </>
  )
}

/** A fixed, always-visible bottom-right pulsing button, like Intercom. */
export function FloatingChatButton() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[999] flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-2xl ring-4 ring-white hover:scale-110 transition-transform animate-pulse-ring"
        aria-label="Открыть чат с AI-ассистентом"
      >
        <svg className="w-6 h-6 sm:w-7 sm:h-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path
            d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      <ChatWidget open={open} onClose={() => setOpen(false)} />
    </>
  )
}
