import { Button } from '../ui/Button'

interface PdfDownloadButtonProps {
  pdfUrl: string | null
}

export function PdfDownloadButton({ pdfUrl }: PdfDownloadButtonProps) {
  if (!pdfUrl) {
    return (
      <div className="flex items-start gap-3 p-4 rounded-xl bg-ink-50 border border-ink-100">
        <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-white border border-ink-200 flex items-center justify-center">
          <svg className="w-5 h-5 text-ink-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round" />
            <polyline points="12 6 12 12 16 14" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-medium text-ink-900">Отчёт ещё не готов</p>
          <p className="text-xs text-ink-500 mt-0.5">
            Как только эксперт завершит аудит — пришлём ссылку и уведомим в Telegram.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4 p-4 rounded-xl bg-gradient-to-br from-emerald-50 to-emerald-100/50 border border-emerald-200">
      <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-emerald-500 text-white flex items-center justify-center shadow-md">
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" strokeLinecap="round" strokeLinejoin="round" />
          <polyline points="14 2 14 8 20 8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-semibold text-ink-900">Отчёт готов</p>
        <p className="text-xs text-emerald-700 mt-0.5">PDF-файл в фирменном стиле</p>
      </div>
      <a href={pdfUrl} target="_blank" rel="noopener noreferrer" download>
        <Button size="md">
          Скачать
          <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 3a1 1 0 011 1v9.586l2.707-2.707a1 1 0 111.414 1.414l-4.414 4.414a1 1 0 01-1.414 0L4.88 12.293a1 1 0 111.414-1.414L9 13.586V4a1 1 0 011-1z" clipRule="evenodd" />
          </svg>
        </Button>
      </a>
    </div>
  )
}
