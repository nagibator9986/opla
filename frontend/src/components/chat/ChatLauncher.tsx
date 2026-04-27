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

/** Большая плавающая кнопка чата в правом нижнем углу. */
export function FloatingChatButton() {
  const [open, setOpen] = useState(false)
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-[999] flex items-center justify-center w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-2xl ring-4 ring-white hover:scale-110 transition-transform animate-pulse-ring"
        aria-label="Открыть чат с Baqsy AI"
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

/**
 * Sticky/docked chat panel — для десктопов: окошко чата зафиксировано в
 * правом нижнем углу (свёрнутая версия), при клике разворачивается в
 * полноценный модальный диалог. На мобиле — обычная плавающая кнопка
 * (FloatingChatButton).
 *
 * Согласно ТЗ: «окошко агента движется справа вдоль всего сайта, пока
 * посетитель скроллит сайт» — `position: fixed` решает задачу: окно
 * остаётся в зоне видимости при любом скролле.
 */
export function DockedChatPanel() {
  const [open, setOpen] = useState(false)
  return (
    <>
      {/* Свёрнутая карточка-привет — десктоп */}
      <div className="hidden lg:block fixed bottom-6 right-6 z-[998] w-72">
        <button
          onClick={() => setOpen(true)}
          className="group w-full rounded-2xl bg-white border border-ink-200/80 shadow-2xl hover:shadow-[0_20px_40px_rgb(15_23_42_/_0.18)] transition-shadow text-left overflow-hidden"
          aria-label="Открыть чат с Baqsy AI"
        >
          <div className="flex items-center gap-3 px-4 py-3.5 bg-gradient-to-r from-ink-900 to-ink-800 text-white">
            <span className="relative flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-brand-400 to-brand-600 shadow-lg flex-shrink-0">
              <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 8V4H8" strokeLinecap="round" strokeLinejoin="round" />
                <rect x="4" y="8" width="16" height="12" rx="2" strokeLinecap="round" strokeLinejoin="round" />
                <path d="M2 14h2M20 14h2M15 13v2M9 13v2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-400 ring-2 ring-ink-800" />
            </span>
            <div className="min-w-0">
              <p className="text-sm font-semibold">Baqsy AI</p>
              <p className="text-[11px] text-ink-300">Онлайн · отвечает мгновенно</p>
            </div>
            <svg
              className="ml-auto w-4 h-4 text-white/60 group-hover:translate-x-0.5 transition-transform"
              viewBox="0 0 20 20" fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="px-4 py-3 text-sm text-ink-700 leading-relaxed">
            Здравствуйте! Помогу подобрать пакет аудита и собрать команду для
            оценки. Нажмите, чтобы начать.
          </div>
        </button>
      </div>

      {/* Мобайл — плавающая круглая кнопка */}
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden fixed bottom-4 right-4 z-[999] flex items-center justify-center w-14 h-14 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 text-white shadow-2xl ring-4 ring-white hover:scale-110 transition-transform animate-pulse-ring"
        aria-label="Открыть чат с Baqsy AI"
      >
        <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
