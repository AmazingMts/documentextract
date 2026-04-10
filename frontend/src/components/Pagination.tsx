import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  page: number
  pages: number
  total: number
  onPage: (p: number) => void
}

export function Pagination({ page, pages, total, onPage }: PaginationProps) {
  if (pages <= 1) return null

  return (
    <div className="flex items-center justify-between py-4">
      <span className="text-sm text-gray-400 dark:text-gray-500">
        Page {page} of {pages} ({total.toLocaleString()} articles)
      </span>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPage(page - 1)}
          disabled={page === 1}
          className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Page numbers — show up to 5 around current */}
        {Array.from({ length: Math.min(5, pages) }, (_, i) => {
          let p: number
          if (pages <= 5) {
            p = i + 1
          } else if (page <= 3) {
            p = i + 1
          } else if (page >= pages - 2) {
            p = pages - 4 + i
          } else {
            p = page - 2 + i
          }
          return (
            <button
              key={p}
              onClick={() => onPage(p)}
              className={`w-9 h-9 text-sm rounded-lg border transition-colors ${
                p === page
                  ? 'bg-indigo-500 border-indigo-500 text-white'
                  : 'border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              {p}
            </button>
          )
        })}

        <button
          onClick={() => onPage(page + 1)}
          disabled={page === pages}
          className="p-2 rounded-lg border border-gray-200 dark:border-gray-700 disabled:opacity-40 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
