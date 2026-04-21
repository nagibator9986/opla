import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught:', error, info)
    }
  }

  handleReset = (): void => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/'
  }

  handleReload = (): void => {
    window.location.reload()
  }

  render() {
    if (!this.state.hasError) return this.props.children
    if (this.props.fallback) return this.props.fallback

    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-50 px-4">
        <div className="max-w-md w-full text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-rose-100 text-rose-600 mb-6">
            <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3m0 3h.01M4.938 19.5h14.124a2 2 0 001.762-2.938L13.76 4.94a2 2 0 00-3.52 0L3.176 16.563A2 2 0 004.938 19.5z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-ink-900 mb-2">Что-то пошло не так</h1>
          <p className="text-ink-600 mb-6">
            Мы уже работаем над этим. Попробуйте обновить страницу или вернуться на главную.
          </p>
          {import.meta.env.DEV && this.state.error && (
            <pre className="text-xs text-left bg-ink-100 text-ink-700 p-3 rounded-lg mb-4 overflow-auto max-h-48">
              {this.state.error.message}
            </pre>
          )}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={this.handleReload}
              className="px-5 py-2.5 rounded-xl bg-ink-900 text-white font-semibold hover:bg-ink-800 transition-colors"
            >
              Обновить страницу
            </button>
            <button
              onClick={this.handleReset}
              className="px-5 py-2.5 rounded-xl border border-ink-200 bg-white text-ink-900 font-semibold hover:bg-ink-50 transition-colors"
            >
              На главную
            </button>
          </div>
        </div>
      </div>
    )
  }
}
