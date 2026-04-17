export function Footer() {
  return (
    <footer className="bg-slate-900 text-white py-10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div>
            <p className="text-lg font-bold">Baqsy System</p>
            <p className="text-slate-400 text-sm mt-1">
              &copy; {new Date().getFullYear()} Baqsy System. Все права защищены.
            </p>
          </div>
          <div className="text-slate-400 text-sm text-center md:text-right">
            <p>Контакты: info@baqsy.kz</p>
            <p className="mt-1">Telegram: @baqsy_bot</p>
          </div>
        </div>
      </div>
    </footer>
  )
}
