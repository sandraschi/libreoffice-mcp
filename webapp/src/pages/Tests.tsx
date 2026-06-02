import { motion } from 'framer-motion'
import { CheckCircle, Loader2, XCircle } from 'lucide-react'
import { useState } from 'react'
import { api, type SelfTestResult } from '../lib/api'
import { useStore } from '../store'

export function TestsPage() {
  const { addToast } = useStore()
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<SelfTestResult | null>(null)

  async function run() {
    setRunning(true)
    try {
      const r = await api.runTests(true)
      setResult(r)
      if (!r.success) {
        addToast({
          type: 'error',
          message: `${r.passed}/${r.total} tests passed`,
        })
      }
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setRunning(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl space-y-6"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-display text-ink-100">Tests</h1>
          <p className="text-sm text-ink-500 mt-1">
            Backend self-tests including optional live soffice convert
          </p>
        </div>
        <button
          type="button"
          onClick={run}
          disabled={running}
          className="px-4 py-2 rounded-lg bg-amber-500 text-ink-950 text-sm hover:bg-amber-400 disabled:opacity-50"
        >
          {running ? 'Running…' : 'Run tests'}
        </button>
      </div>

      {running && (
        <div className="flex items-center gap-2 text-ink-500 text-sm">
          <Loader2 size={16} className="animate-spin" /> Running self-tests…
        </div>
      )}

      {result && (
        <div className="bg-ink-900 border border-ink-700 rounded-lg divide-y divide-ink-800">
          <div className="px-4 py-3 text-sm text-ink-300">
            {result.passed}/{result.total} passed
            {result.success ? (
              <CheckCircle size={14} className="inline ml-2 text-acid" />
            ) : (
              <XCircle size={14} className="inline ml-2 text-red-400" />
            )}
          </div>
          {result.results.map((row) => (
            <div
              key={row.name}
              className="px-4 py-2.5 flex items-start gap-3 text-sm"
            >
              {row.ok ? (
                <CheckCircle size={14} className="text-acid mt-0.5 shrink-0" />
              ) : (
                <XCircle size={14} className="text-red-400 mt-0.5 shrink-0" />
              )}
              <div>
                <p className="font-mono text-ink-300">{row.name}</p>
                {row.detail && (
                  <p className="text-xs text-ink-500 mt-0.5 break-all">
                    {row.detail}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  )
}
