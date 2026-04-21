import { cn } from '../../lib/cn'

interface StatusProgressProps {
  status: string
}

interface Step {
  key: string
  label: string
  desc: string
  statuses: string[]
}

const STEPS: Step[] = [
  {
    key: 'paid',
    label: 'Оплачено',
    desc: 'Платёж подтверждён',
    statuses: ['paid', 'in_progress_basic'],
  },
  {
    key: 'questionnaire',
    label: 'Анкета',
    desc: 'Отвечаете на вопросы',
    statuses: ['in_progress_full'],
  },
  {
    key: 'audit',
    label: 'Аудит',
    desc: 'Эксперт готовит отчёт',
    statuses: ['completed', 'under_audit'],
  },
  {
    key: 'delivered',
    label: 'Готово',
    desc: 'Отчёт доставлен',
    statuses: ['delivered'],
  },
]

function getActiveStep(status: string): number {
  const idx = STEPS.findIndex((s) => s.statuses.includes(status))
  if (idx === -1) return 0
  return idx
}

const STATUS_LABELS: Record<string, string> = {
  created: 'Новый заказ',
  in_progress_basic: 'Онбординг',
  paid: 'Оплачен',
  in_progress_full: 'Заполнение анкеты',
  completed: 'Анкета завершена',
  under_audit: 'На аудите',
  delivered: 'Доставлен',
}

export function StatusProgress({ status }: StatusProgressProps) {
  const activeStep = getActiveStep(status)
  const statusLabel = STATUS_LABELS[status] ?? status
  const progress = STEPS.length > 0 ? ((activeStep + 1) / STEPS.length) * 100 : 0

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-ink-500">
          Текущий статус
        </span>
        <span className="text-sm font-semibold text-ink-900">{statusLabel}</span>
      </div>

      {/* Desktop: horizontal with connector */}
      <div className="hidden md:block relative">
        <div className="absolute top-5 left-5 right-5 h-1 bg-ink-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-400 to-brand-500 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${Math.max(0, (activeStep / (STEPS.length - 1)) * 100)}%` }}
          />
        </div>
        <div className="relative grid grid-cols-4 gap-2">
          {STEPS.map((step, i) => {
            const isCompleted = i < activeStep
            const isCurrent = i === activeStep
            return (
              <div key={step.key} className="flex flex-col items-center">
                <div
                  className={cn(
                    'relative flex items-center justify-center w-10 h-10 rounded-full border-2 font-bold text-sm transition-all duration-300',
                    isCompleted && 'bg-emerald-500 border-emerald-500 text-white',
                    isCurrent && 'bg-brand-500 border-brand-500 text-white animate-pulse-ring',
                    !isCompleted && !isCurrent && 'bg-white border-ink-200 text-ink-400',
                  )}
                >
                  {isCompleted ? (
                    <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={cn(
                    'mt-3 text-sm font-semibold text-center',
                    isCompleted || isCurrent ? 'text-ink-900' : 'text-ink-400',
                  )}
                >
                  {step.label}
                </span>
                <span
                  className={cn(
                    'mt-1 text-xs text-center',
                    isCompleted || isCurrent ? 'text-ink-500' : 'text-ink-400',
                  )}
                >
                  {step.desc}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Mobile: vertical list */}
      <div className="md:hidden">
        <div className="mb-3 h-2 rounded-full bg-ink-100 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-emerald-400 to-brand-500 rounded-full transition-all duration-700 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <ul className="space-y-2.5">
          {STEPS.map((step, i) => {
            const isCompleted = i < activeStep
            const isCurrent = i === activeStep
            return (
              <li key={step.key} className="flex items-center gap-3">
                <div
                  className={cn(
                    'flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full border-2 font-bold text-xs transition-colors',
                    isCompleted && 'bg-emerald-500 border-emerald-500 text-white',
                    isCurrent && 'bg-brand-500 border-brand-500 text-white',
                    !isCompleted && !isCurrent && 'bg-white border-ink-200 text-ink-400',
                  )}
                >
                  {isCompleted ? (
                    <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    i + 1
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      'text-sm font-semibold',
                      isCompleted || isCurrent ? 'text-ink-900' : 'text-ink-400',
                    )}
                  >
                    {step.label}
                  </p>
                  <p className={cn('text-xs', isCompleted || isCurrent ? 'text-ink-500' : 'text-ink-400')}>
                    {step.desc}
                  </p>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
