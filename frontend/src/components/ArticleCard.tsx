import { useState } from 'react'
import { ExternalLink, Clock, ChevronDown, ChevronUp, Cpu } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { Article, parseTopics } from '../api/articles'

const COMPANY_COLORS: Record<string, string> = {
  Google: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Meta: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-200',
  Netflix: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Uber: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200',
  Airbnb: 'bg-rose-100 text-rose-700 dark:bg-rose-900/40 dark:text-rose-300',
  LinkedIn: 'bg-sky-100 text-sky-700 dark:bg-sky-900/40 dark:text-sky-300',
  AWS: 'bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300',
  Microsoft: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
  Cloudflare: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-200',
  Stripe: 'bg-violet-100 text-violet-700 dark:bg-violet-900/40 dark:text-violet-300',
  Discord: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300',
  Dropbox: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
  Databricks: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200',
  Confluent: 'bg-teal-100 text-teal-700 dark:bg-teal-900/40 dark:text-teal-300',
  Pinterest: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  Shopify: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
}

const DEFAULT_COLOR = 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'

function formatSummary(text: string) {
  // Convert **bold** to <strong> and render line breaks
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br />')
}

interface ArticleCardProps {
  article: Article
  onTopicClick?: (topic: string) => void
}

export function ArticleCard({ article, onTopicClick }: ArticleCardProps) {
  const [expanded, setExpanded] = useState(false)
  const topics = parseTopics(article.topics)
  const companyColor = (article.company && COMPANY_COLORS[article.company]) || DEFAULT_COLOR

  const publishedStr = article.published_at
    ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true })
    : null

  const readMinutes = article.word_count ? Math.max(1, Math.round(article.word_count / 200)) : null

  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-5 hover:border-indigo-300 dark:hover:border-indigo-700 transition-colors">
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 flex-wrap">
          {article.company && (
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${companyColor}`}>
              {article.company}
            </span>
          )}
          {publishedStr && (
            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {publishedStr}
            </span>
          )}
          {readMinutes && (
            <span className="text-xs text-gray-400 dark:text-gray-500">
              {readMinutes} min read
            </span>
          )}
        </div>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-indigo-500 transition-colors"
          title="Open original article"
        >
          <ExternalLink className="w-4 h-4" />
        </a>
      </div>

      {/* Title */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="block font-semibold text-gray-900 dark:text-gray-100 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors mb-2 leading-snug"
      >
        {article.title}
      </a>

      {article.author && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mb-3">by {article.author}</p>
      )}

      {/* Topic chips */}
      {topics.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-3">
          {topics.map(t => (
            <button
              key={t}
              onClick={() => onTopicClick?.(t)}
              className="text-xs px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
            >
              {t}
            </button>
          ))}
        </div>
      )}

      {/* AI Summary */}
      {article.summary && (
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-1.5 text-xs text-indigo-500 dark:text-indigo-400 font-medium">
              <Cpu className="w-3 h-3" />
              AI Summary
            </div>
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              {expanded ? (
                <><ChevronUp className="w-3 h-3" /> Collapse</>
              ) : (
                <><ChevronDown className="w-3 h-3" /> Expand</>
              )}
            </button>
          </div>
          <div
            className={`prose-summary overflow-hidden transition-all duration-200 ${
              expanded ? 'max-h-none' : 'max-h-32'
            }`}
            dangerouslySetInnerHTML={{ __html: formatSummary(article.summary) }}
          />
          {!expanded && (
            <div className="h-8 bg-gradient-to-t from-white dark:from-gray-900 to-transparent -mt-8 relative pointer-events-none" />
          )}
        </div>
      )}
    </div>
  )
}
