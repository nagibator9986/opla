import type { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  highlight?: boolean
}

export function Card({ children, className = '', highlight = false }: CardProps) {
  return (
    <div
      className={`rounded-2xl p-6 md:p-8 ${
        highlight
          ? 'bg-slate-900 text-white shadow-2xl ring-2 ring-amber-500'
          : 'bg-white shadow-lg border border-slate-200'
      } ${className}`}
    >
      {children}
    </div>
  )
}
