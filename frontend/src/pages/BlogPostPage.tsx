import { Link, useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Header } from '../components/layout/Header'
import { Footer } from '../components/layout/Footer'
import { Container } from '../components/ui/Container'
import { Badge } from '../components/ui/Badge'
import { DockedChatPanel } from '../components/chat/ChatLauncher'
import { getBlogPost } from '../api/blog'

export function BlogPostPage() {
  const { slug } = useParams<{ slug: string }>()
  const { data, isLoading, isError } = useQuery({
    queryKey: ['blog', slug],
    queryFn: () => getBlogPost(slug!),
    enabled: !!slug,
    retry: 1,
  })

  return (
    <div className="flex flex-col min-h-screen bg-white">
      <Header variant="solid" />
      <main className="flex-1 pt-24 pb-16 md:pt-28">
        <Container size="sm">
          <Link
            to="/#blog"
            className="inline-flex items-center gap-1 text-sm font-semibold text-ink-600 hover:text-ink-900 mb-6"
          >
            <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                clipRule="evenodd"
              />
            </svg>
            Все материалы
          </Link>

          {isLoading && <PostSkeleton />}
          {(isError || (!isLoading && !data)) && (
            <div className="py-20 text-center">
              <h1 className="text-2xl font-bold text-ink-900 mb-2">Запись не найдена</h1>
              <p className="text-ink-600 mb-6">
                Возможно, она была снята с публикации или ссылка устарела.
              </p>
            </div>
          )}

          {data && (
            <article className="animate-fade-in">
              <header className="mb-8">
                <Badge variant="brand" className="mb-4">
                  {data.category_label}
                </Badge>
                <h1 className="text-3xl md:text-5xl font-bold text-ink-900 tracking-tight leading-[1.1]">
                  {data.title}
                </h1>
                <div className="mt-4 flex items-center gap-3 text-sm text-ink-500">
                  <span>{data.reading_time_min} мин чтения</span>
                  {data.published_at && (
                    <>
                      <span>·</span>
                      <time>
                        {new Date(data.published_at).toLocaleDateString('ru-RU', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric',
                        })}
                      </time>
                    </>
                  )}
                </div>
              </header>

              {data.cover_url && (
                <img
                  src={data.cover_url}
                  alt={data.title}
                  className="w-full rounded-2xl mb-10 object-cover"
                />
              )}

              {data.excerpt && (
                <p className="text-lg md:text-xl text-ink-700 leading-relaxed mb-8 font-medium border-l-4 border-brand-400 pl-5">
                  {data.excerpt}
                </p>
              )}

              <div className="prose prose-ink max-w-none text-ink-800 leading-relaxed whitespace-pre-wrap text-base md:text-lg">
                {data.body || 'Полный текст скоро появится.'}
              </div>
            </article>
          )}
        </Container>
      </main>
      <Footer />
      <DockedChatPanel />
    </div>
  )
}

function PostSkeleton() {
  return (
    <div className="animate-pulse py-6 space-y-4">
      <div className="h-6 w-32 bg-ink-100 rounded" />
      <div className="h-12 bg-ink-100 rounded w-3/4" />
      <div className="h-5 bg-ink-100 rounded w-2/5" />
      <div className="h-64 bg-ink-100 rounded mt-8" />
      <div className="space-y-2">
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded w-5/6" />
      </div>
    </div>
  )
}
