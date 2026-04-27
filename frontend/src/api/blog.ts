import api from './axios'

export type BlogCategory = 'article' | 'glossary' | 'philosophy'

export interface BlogPostSummary {
  slug: string
  title: string
  excerpt: string
  category: BlogCategory
  category_label: string
  cover_url: string | null
  reading_time_min: number
  published_at: string | null
}

export interface BlogPostDetail extends BlogPostSummary {
  body: string
}

export async function listBlogPosts(): Promise<BlogPostSummary[]> {
  const { data } = await api.get<BlogPostSummary[] | { results: BlogPostSummary[] }>('/blog/')
  return Array.isArray(data) ? data : data.results
}

export async function getBlogPost(slug: string): Promise<BlogPostDetail> {
  const { data } = await api.get<BlogPostDetail>(`/blog/${slug}/`)
  return data
}
