interface StatusProgressProps {
  status: string
}

const STEPS = [
  { label: 'Оплачено', statuses: ['paid', 'in_progress_basic'] },
  { label: 'Анкета', statuses: ['in_progress_full'] },
  { label: 'На аудите', statuses: ['completed', 'under_audit'] },
  { label: 'Готово', statuses: ['delivered'] },
]

function getActiveStep(status: string): number {
  const idx = STEPS.findIndex((s) => s.statuses.includes(status))
  if (idx === -1) return 0
  return idx
}

export function StatusProgress({ status }: StatusProgressProps) {
  const activeStep = getActiveStep(status)

  return (
    <div className="w-full">
      {/* Desktop: horizontal */}
      <div className="hidden md:flex items-start justify-between relative">
        {/* Connecting line */}
        <div className="absolute top-5 left-0 right-0 h-0.5 bg-slate-200 z-0" />
        {STEPS.map((step, i) => {
          const isCompleted = i < activeStep
          const isCurrent = i === activeStep
          const isFuture = i > activeStep
          return (
            <div key={step.label} className="flex flex-col items-center z-10 flex-1 first:items-start last:items-end">
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                  isCompleted
                    ? 'bg-emerald-500 text-white'
                    : isCurrent
                    ? 'bg-amber-500 text-white animate-pulse'
                    : isFuture
                    ? 'bg-slate-300 text-slate-500'
                    : ''
                }`}
              >
                {isCompleted ? (
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`mt-2 text-xs font-medium text-center ${
                  isCompleted || isCurrent ? 'text-slate-900' : 'text-slate-400'
                }`}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Mobile: vertical */}
      <div className="flex flex-col gap-3 md:hidden">
        {STEPS.map((step, i) => {
          const isCompleted = i < activeStep
          const isCurrent = i === activeStep
          const isFuture = i > activeStep
          return (
            <div key={step.label} className="flex items-center gap-4">
              <div
                className={`w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                  isCompleted
                    ? 'bg-emerald-500 text-white'
                    : isCurrent
                    ? 'bg-amber-500 text-white animate-pulse'
                    : isFuture
                    ? 'bg-slate-300 text-slate-500'
                    : ''
                }`}
              >
                {isCompleted ? (
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              <span
                className={`text-sm font-medium ${
                  isCompleted || isCurrent ? 'text-slate-900' : 'text-slate-400'
                }`}
              >
                {step.label}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
