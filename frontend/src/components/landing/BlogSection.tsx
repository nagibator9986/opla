import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { Container, Section } from '../ui/Container'
import { Badge } from '../ui/Badge'
import { listBlogPosts, type BlogCategory, type BlogPostSummary } from '../../api/blog'

const CATEGORY_BADGE: Record<BlogCategory, string> = {
  article: 'bg-sky-100 text-sky-800 ring-sky-200',
  glossary: 'bg-amber-100 text-amber-900 ring-amber-200',
  philosophy: 'bg-violet-100 text-violet-800 ring-violet-200',
}

export function BlogSection() {
  const { data: posts, isLoading } = useQuery({
    queryKey: ['blog'],
    queryFn: listBlogPosts,
    staleTime: 5 * 60 * 1000,
  })

  // Show only first 3 on landing
  const visible = (posts ?? []).slice(0, 3)

  return (
    <Section id="blog" background="white">
      <Container>
        <div className="flex items-end justify-between flex-wrap gap-4 mb-10 md:mb-12">
          <div className="max-w-xl">
            <Badge variant="neutral" className="mb-4">
              Информационный блок
            </Badge>
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-ink-900 tracking-tight">
              Статьи
            </h2>
            <p className="mt-3 text-base md:text-lg text-ink-600 leading-relaxed">
              Материалы о методе Baqsy и Коде Вечного Иля — для тех, кто хочет
              понять подход глубже перед аудитом.
            </p>
          </div>
          {visible.length > 0 && (
            <Link
              to="/blog"
              className="inline-flex items-center gap-1 text-sm font-semibold text-brand-700 hover:text-brand-600"
            >
              Все материалы
              <svg className="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
          )}
        </div>

        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <BlogPostSkeleton key={i} />
            ))}
          </div>
        ) : visible.length === 0 ? (
          <div className="text-center py-12 text-ink-500 bg-ink-50 rounded-2xl">
            Скоро здесь появятся первые статьи.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {visible.map((post) => (
              <BlogPostCard key={post.slug} post={post} />
            ))}
          </div>
        )}
      </Container>
    </Section>
  )
}

function BlogPostCard({ post }: { post: BlogPostSummary }) {
  return (
    <Link
      to={`/blog/${post.slug}`}
      className="group flex flex-col bg-white rounded-2xl overflow-hidden border border-ink-200 hover:border-brand-300 hover:shadow-[0_10px_30px_rgb(15_23_42_/_0.1)] hover:-translate-y-1 transition-all duration-300"
    >
      <div className="relative aspect-[16/10] bg-ink-100 overflow-hidden">
        {post.cover_url ? (
          <img
            src={post.cover_url}
            alt={post.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-ink-100 to-ink-200" />
        )}
        <span
          className={`absolute top-3 left-3 inline-flex items-center px-2.5 py-1 rounded-full ring-1 text-[11px] font-semibold uppercase tracking-wide ${CATEGORY_BADGE[post.category]}`}
        >
          {post.category_label}
        </span>
      </div>
      <div className="flex flex-col flex-1 p-5">
        <h3 className="text-lg font-bold text-ink-900 mb-2 leading-snug group-hover:text-brand-700 transition-colors">
          {post.title}
        </h3>
        {post.excerpt && (
          <p className="text-sm text-ink-600 leading-relaxed line-clamp-3">
            {post.excerpt}
          </p>
        )}
        <div className="mt-4 pt-4 border-t border-ink-100 flex items-center justify-between text-xs text-ink-500">
          <span>{post.reading_time_min} мин чтения</span>
          <span className="font-semibold text-brand-700 group-hover:text-brand-600">
            Читать →
          </span>
        </div>
      </div>
    </Link>
  )
}

function BlogPostSkeleton() {
  return (
    <div className="rounded-2xl bg-white border border-ink-200 overflow-hidden animate-pulse">
      <div className="aspect-[16/10] bg-ink-100" />
      <div className="p-5 space-y-3">
        <div className="h-5 bg-ink-100 rounded w-4/5" />
        <div className="h-4 bg-ink-100 rounded" />
        <div className="h-4 bg-ink-100 rounded w-3/4" />
      </div>
    </div>
  )
}
