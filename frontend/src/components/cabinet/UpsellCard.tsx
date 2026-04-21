import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '../ui/Button'
import { useToast } from '../ui/toast-context'
import { initiateUpsell } from '../../api/payments'
import { openPaymentWidget } from '../payment/openPaymentWidget'

interface UpsellCardProps {
  submissionId: string
  tariffCode: string | null
  status: string
}

const UPSELL_VISIBLE_STATUSES = ['completed', 'under_audit', 'delivered']

const BENEFITS = [
  'Полный разбор по 18–24 параметрам',
  'Глубокая аналитика по каждому блоку',
  'Персональные рекомендации эксперта',
]

export function UpsellCard({ submissionId, tariffCode, status }: UpsellCardProps) {
  const [loading, setLoading] = useState(false)
  const queryClient = useQueryClient()
  const toast = useToast()

  if (tariffCode !== 'ashide_1' || !UPSELL_VISIBLE_STATUSES.includes(status)) {
    return null
  }

  const handleUpsell = async () => {
    setLoading(true)
    try {
      const config = await initiateUpsell(submissionId)
      openPaymentWidget(
        config,
        () => {
          queryClient.invalidateQueries({ queryKey: ['my-submission'] })
          toast.show({
            kind: 'success',
            title: 'Тариф обновлён',
            description: 'Расширенный аудит уже в работе.',
          })
          setLoading(false)
        },
        (reason) => {
          toast.show({
            kind: 'error',
            title: 'Оплата не прошла',
            description: reason || 'Попробуйте ещё раз.',
          })
          setLoading(false)
        },
      )
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Не удалось инициировать оплату. Попробуйте позже.'
      toast.show({ kind: 'error', title: 'Ошибка', description: message })
      setLoading(false)
    }
  }

  return (
    <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 text-white p-6 md:p-8 shadow-xl">
      <div
        aria-hidden
        className="absolute -top-20 -right-20 w-56 h-56 rounded-full bg-brand-500/25 blur-3xl"
      />
      <div className="relative">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 ring-1 ring-brand-400/30 text-xs font-semibold mb-4">
          <svg className="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" />
          </svg>
          Апгрейд
        </div>

        <h3 className="text-xl md:text-2xl font-bold mb-2">Расширьте до Ashide 2</h3>
        <p className="text-ink-300 text-sm md:text-base mb-5 leading-relaxed">
          Получите максимальную глубину аудита — без повторного заполнения анкеты.
        </p>

        <ul className="space-y-2.5 mb-6">
          {BENEFITS.map((b) => (
            <li key={b} className="flex items-start gap-2.5 text-sm text-ink-200">
              <svg
                className="w-5 h-5 flex-shrink-0 text-brand-400 mt-px"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>{b}</span>
            </li>
          ))}
        </ul>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pt-5 border-t border-white/10">
          <div>
            <p className="text-xs uppercase tracking-wider text-ink-400 mb-1">Доплата</p>
            <p className="text-2xl font-bold">
              90 000 <span className="text-brand-300 text-lg">₸</span>
            </p>
          </div>
          <Button
            variant="secondary"
            size="lg"
            onClick={handleUpsell}
            loading={loading}
          >
            Расширить тариф
          </Button>
        </div>
      </div>
    </div>
  )
}
