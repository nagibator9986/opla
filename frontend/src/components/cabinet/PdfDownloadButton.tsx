import { Button } from '../ui/Button'

interface PdfDownloadButtonProps {
  pdfUrl: string | null
}

export function PdfDownloadButton({ pdfUrl }: PdfDownloadButtonProps) {
  if (!pdfUrl) {
    return <p className="text-slate-400 text-sm">Отчёт ещё не готов</p>
  }

  return (
    <a href={pdfUrl} target="_blank" rel="noopener noreferrer">
      <Button variant="primary">Скачать отчёт</Button>
    </a>
  )
}
