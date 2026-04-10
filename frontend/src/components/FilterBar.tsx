import { useEffect, useRef } from 'react'
import { Search, X } from 'lucide-react'

interface FilterBarProps {
  companies: string[]
  topics: string[]
  selectedCompany: string
  selectedTopic: string
  searchQuery: string
  sort: 'newest' | 'oldest'
  onCompanyChange: (v: string) => void
  onTopicChange: (v: string) => void
  onSearchChange: (v: string) => void
  onSortChange: (v: 'newest' | 'oldest') => void
  onClear: () => void
}

export function FilterBar({
  companies, topics, selectedCompany, selectedTopic,
  searchQuery, sort, onCompanyChange, onTopicChange,
  onSearchChange, onSortChange, onClear,
}: FilterBarProps) {
  const searchRef = useRef<HTMLInputElement>(null)
  const hasFilter = selectedCompany || selectedTopic || searchQuery

  return (
    <div className="space-y-3">
      {/* Search + sort row */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            ref={searchRef}
            type="text"
            value={searchQuery}
            onChange={e => onSearchChange(e.target.value)}
            placeholder="Search articles..."
            className="w-full pl-9 pr-4 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={sort}
          onChange={e => onSortChange(e.target.value as 'newest' | 'oldest')}
          className="px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
        </select>
        {hasFilter && (
          <button
            onClick={onClear}
            className="flex items-center gap-1 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <X className="w-3 h-3" /> Clear
          </button>
        )}
      </div>

      {/* Company + topic filter row */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={selectedCompany}
          onChange={e => onCompanyChange(e.target.value)}
          className="px-3 py-1.5 text-sm rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All companies</option>
          {companies.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <div className="flex flex-wrap gap-1.5">
          {topics.slice(0, 20).map(t => (
            <button
              key={t}
              onClick={() => onTopicChange(selectedTopic === t ? '' : t)}
              className={`px-2.5 py-1 text-xs rounded-full border transition-colors ${
                selectedTopic === t
                  ? 'bg-indigo-500 border-indigo-500 text-white'
                  : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600 text-gray-600 dark:text-gray-400'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
