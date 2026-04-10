import { useState, useEffect } from 'react'
import { Zap, Moon, Sun } from 'lucide-react'

export function Header() {
  const [dark, setDark] = useState(() =>
    window.matchMedia('(prefers-color-scheme: dark)').matches
  )

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  return (
    <header className="sticky top-0 z-10 bg-white/90 dark:bg-gray-900/90 backdrop-blur border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-indigo-500" />
          <span className="font-semibold text-lg tracking-tight">DistSys Feed</span>
          <span className="hidden sm:inline text-xs text-gray-400 dark:text-gray-500 ml-2">
            Distributed systems engineering, daily
          </span>
        </div>
        <button
          onClick={() => setDark(!dark)}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Toggle dark mode"
        >
          {dark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  )
}
