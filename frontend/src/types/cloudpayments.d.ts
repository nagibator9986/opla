export {}

declare global {
  interface Window {
    cp: {
      CloudPayments: new () => {
        pay: (
          mode: 'charge',
          options: CloudPaymentsOptions,
          callbacks: CloudPaymentsCallbacks,
        ) => void
      }
    }
  }
}

interface CloudPaymentsOptions {
  publicId: string
  description: string
  amount: number
  currency: string
  invoiceId: string
  accountId: string
  data?: Record<string, unknown>
}

interface CloudPaymentsCallbacks {
  onSuccess?: (options: CloudPaymentsOptions) => void
  onFail?: (reason: string, options: CloudPaymentsOptions) => void
}
