interface PaymentOptions {
  publicId: string
  amount: number
  currency: string
  invoiceId: string
  description: string
  accountId: string
  data?: Record<string, unknown>
}

export function openPaymentWidget(
  options: PaymentOptions,
  onSuccess: () => void,
  onFail?: (reason: string) => void,
): void {
  if (!options.publicId) {
    onFail?.('Платёжный модуль не настроен. Обратитесь в поддержку.')
    return
  }
  if (!window.cp?.CloudPayments) {
    onFail?.('Платёжный модуль не загружен. Обновите страницу.')
    return
  }
  const widget = new window.cp.CloudPayments()
  widget.pay('charge', options, {
    onSuccess: () => onSuccess(),
    onFail: (reason: string) => onFail?.(reason),
  })
}
