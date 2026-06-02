import { motion } from 'framer-motion'
import {
  AlertCircle,
  AlertTriangle,
  Bug,
  Filter,
  Info,
  ScrollText,
  Terminal,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, type LogEntry } from '../lib/api'

function levelIcon(level: string) {
  switch (level) {
    case 'ERROR':
      return <AlertCircle size={14} className="text-red-400" />
    case 'WARNING':
      return <AlertTriangle size={14} className="text-amber-400" />
    case 'DEBUG':
      return <Bug size={14} className="text-blue-400" />
    default:
      return <Info size={14} className="text-ink-500" />
  }
}

export function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [filter, setFilter] = useState('')
  const [levelFilter, setLevelFilter] = useState<string | null>(null)
  const [fetching, setFetching] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setFetching(true)
      try {
        const data = await api.logs()
        if (!cancelled) setLogs(data.logs)
      } catch {
        /* backend may be starting */
      } finally {
        if (!cancelled) setFetching(false)
      }
    }
    load()
    const timer = window.setInterval(load, 3000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  const filtered = logs.filter((log) => {
    const text = filter.toLowerCase()
    const matchesText =
      log.message.toLowerCase().includes(text) ||
      log.name.toLowerCase().includes(text)
    const matchesLevel = levelFilter ? log.level === levelFilter : true
    return matchesText && matchesLevel
  })

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [filtered.length])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-[calc(100vh-8rem)] space-y-4"
    >
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-2">
          <Terminal size={18} className="text-amber-400" />
          <h1 className="text-xl font-display text-ink-100">Logs</h1>
          {fetching && (
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
          )}
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Filter
              size={14}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-ink-600"
            />
            <input
              type="text"
              placeholder="Filter…"
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="bg-ink-950 border border-ink-700 rounded-md pl-8 pr-3 py-1.5 text-xs text-ink-200 w-48 focus:outline-none focus:border-amber-500"
            />
          </div>
          <div className="flex bg-ink-900 border border-ink-700 rounded-md p-0.5">
            {['ERROR', 'WARNING', 'INFO', 'DEBUG'].map((lvl) => (
              <button
                key={lvl}
                type="button"
                onClick={() => setLevelFilter(levelFilter === lvl ? null : lvl)}
                className={`px-2 py-0.5 text-[10px] font-bold rounded ${
                  levelFilter === lvl
                    ? 'bg-amber-500/20 text-amber-400'
                    : 'text-ink-600 hover:text-ink-400'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => api.logs().then((d) => setLogs(d.logs))}
            className="p-2 rounded-md border border-ink-700 text-ink-500 hover:text-amber-400"
          >
            <ScrollText size={14} />
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 bg-ink-950 border border-ink-800 rounded-lg overflow-y-auto font-mono text-xs p-4"
      >
        {filtered.length === 0 ? (
          <div className="h-full flex items-center justify-center text-ink-600 italic">
            No log entries yet
          </div>
        ) : (
          <div className="space-y-1">
            {filtered.map((log) => (
              <div
                key={`${log.timestamp}-${log.level}-${log.name}-${log.message.slice(0, 40)}`}
                className="flex gap-3 py-0.5 hover:bg-ink-900/80 px-1 rounded"
              >
                <span className="text-ink-600 shrink-0">
                  {new Date(log.timestamp).toLocaleTimeString([], {
                    hour12: false,
                  })}
                </span>
                <span className="shrink-0 flex items-center gap-1 w-20">
                  {levelIcon(log.level)}
                  <span className="font-bold">{log.level}</span>
                </span>
                <span className="text-amber-500/70 shrink-0">[{log.name}]</span>
                <span className="text-ink-300 break-all">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
      <div className="text-[10px] text-ink-600 uppercase tracking-wider">
        {filtered.length} entries · auto-refresh 3s
      </div>
    </motion.div>
  )
}
