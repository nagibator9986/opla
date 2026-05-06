export function PageFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div
        className="w-12 h-12 rounded-full border-4 border-ink-200 border-t-brand-500 animate-spin"
        role="status"
        aria-label="Загрузка"
      />
    </div>
  )
}
