import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Card } from '../ui/Card'
import { Button } from '../ui/Button'
import { initiateUpsell } from '../../api/payments'
import { openPaymentWidget } from '../payment/openPaymentWidget'

interface UpsellCardProps {
  submissionId: string
  tariffCode: string | null
  status: string
}

const UPSELL_VISIBLE_STATUSES = ['completed', 'under_audit', 'delivered']

export function UpsellCard({ submissionId, tariffCode, status }: UpsellCardProps) {
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const queryClient = useQueryClient()

  if (tariffCode !== 'ashide_1' || !UPSELL_VISIBLE_STATUSES.includes(status)) {
    return null
  }

  const handleUpsell = async () => {
    setLoading(true)
    setApiError(null)
    try {
      const config = await initiateUpsell(submissionId)
      openPaymentWidget(
        config,
        () => {
          queryClient.invalidateQueries({ queryKey: ['my-submission'] })
          alert('Тариф обновлён!')
        },
        (reason) => {
          alert(`Оплата не прошла: ${reason}`)
        },
      )
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Не удалось инициализировать оплату. Попробуйте позже.'
      setApiError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card highlight={false}>
      <h3 className="text-lg font-bold text-slate-900 mb-2">Расширьте до Ashide 2</h3>
      <p className="text-slate-600 text-sm mb-4">
        Получите полный анализ по 18-24 параметрам. Доплата 90 000 ₸
      </p>
      {apiError && <p className="text-red-600 text-sm mb-3">{apiError}</p>}
      <Button variant="secondary" onClick={handleUpsell} disabled={loading}>
        {loading ? 'Загрузка...' : 'Расширить тариф'}
      </Button>
    </Card>
  )
}
