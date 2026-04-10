export interface Article {
  id: number
  url: string
  title: string
  author: string | null
  published_at: string | null
  crawled_at: string
  summary: string | null
  topics: string // JSON string
  word_count: number | null
  company: string | null
  source_name: string | null
}

export interface ArticleListResponse {
  items: Article[]
  total: number
  page: number
  pages: number
  companies: string[]
  topics: string[]
  updatedAt: string | null
}

export interface ArticleFilters {
  page?: number
  limit?: number
  company?: string
  topic?: string
  q?: string
  sort?: 'newest' | 'oldest'
}

// Cache the raw articles so we only fetch once per session
let _cache: Article[] | null = null

async function loadAll(): Promise<Article[]> {
  if (_cache) return _cache
  const res = await fetch('./articles.json')
  if (!res.ok) throw new Error(`Failed to load articles.json: HTTP ${res.status}`)
  _cache = await res.json()
  return _cache!
}

export async function fetchArticles(filters: ArticleFilters = {}): Promise<ArticleListResponse> {
  const {
    page = 1,
    limit = 20,
    company,
    topic,
    q,
    sort = 'newest',
  } = filters

  let all = await loadAll()

  // Filter
  if (company) all = all.filter(a => a.company === company)
  if (topic) all = all.filter(a => a.topics.toLowerCase().includes(topic.toLowerCase()))
  if (q) {
    const ql = q.toLowerCase()
    all = all.filter(a =>
      a.title.toLowerCase().includes(ql) ||
      (a.summary ?? '').toLowerCase().includes(ql)
    )
  }

  // Sort
  all = [...all].sort((a, b) => {
    const da = a.published_at ? new Date(a.published_at).getTime() : 0
    const db = b.published_at ? new Date(b.published_at).getTime() : 0
    return sort === 'newest' ? db - da : da - db
  })

  const total = all.length
  const pages = Math.max(1, Math.ceil(total / limit))
  const offset = (page - 1) * limit
  const items = all.slice(offset, offset + limit)

  // Build filter options from full unfiltered dataset
  const everything = await loadAll()
  const companySet = new Set(everything.map(a => a.company).filter(Boolean) as string[])

  const topicCounter: Record<string, number> = {}
  for (const a of everything) {
    try {
      for (const t of JSON.parse(a.topics)) {
        topicCounter[t] = (topicCounter[t] ?? 0) + 1
      }
    } catch {}
  }
  const topTopics = Object.keys(topicCounter).sort((a, b) => topicCounter[b] - topicCounter[a]).slice(0, 30)

  // Try to get last updated time from newest article
  const latest = everything[0]?.crawled_at ?? null

  return {
    items,
    total,
    page,
    pages,
    companies: [...companySet].sort(),
    topics: topTopics,
    updatedAt: latest,
  }
}

export function parseTopics(topicsJson: string): string[] {
  try {
    return JSON.parse(topicsJson)
  } catch {
    return []
  }
}
