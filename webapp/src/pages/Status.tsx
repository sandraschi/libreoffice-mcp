import { CheckCircle, RefreshCw, Server, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type Health } from '../lib/api'
import { useStore } from '../store'

function Row({
  label,
  value,
  mono,
}: {
  label: string
  value: React.ReactNode
  mono?: boolean
}) {
  return (
    <div className="flex items-start justify-between py-2.5 border-b border-ink-800/60 last:border-0 gap-4">
      <span className="text-xs text-ink-500 flex-shrink-0 w-44">{label}</span>
      <span
        className={[
          'text-xs text-right flex-1',
          mono ? 'font-mono text-ink-300' : 'text-ink-300',
        ].join(' ')}
      >
        {value}
      </span>
    </div>
  )
}

export function Status() {
  const { addToast, setHealth } = useStore()
  const [health, setLocalHealth] = useState<Health | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api
      .health()
      .then((h) => {
        setLocalHealth(h)
        setHealth(h)
      })
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [addToast, setHealth])

  return (
    <div className="space-y-5 max-w-2xl">
      <div className="flex items-center justify-between">
        <h2 className="text-xs text-ink-500 uppercase tracking-wider">
          System audit
        </h2>
        <button
          type="button"
          onClick={load}
          className="text-ink-500 hover:text-amber-400 text-xs flex items-center gap-1"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />{' '}
          Refresh
        </button>
      </div>

      {health && (
        <>
          <div className="bg-ink-900 border border-ink-700 rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-ink-700 flex items-center gap-2">
              <Server size={13} className="text-amber-400" />
              <span className="text-sm text-ink-200">Backend :10981</span>
            </div>
            <div className="px-4 py-1">
              <Row label="MCP version" value={health.version} mono />
              <Row
                label="LibreOffice"
                value={
                  <span
                    className={
                      health.soffice_available ? 'text-acid' : 'text-red-400'
                    }
                  >
                    {health.soffice_available ? (
                      <CheckCircle size={11} className="inline mr-1" />
                    ) : (
                      <XCircle size={11} className="inline mr-1" />
                    )}
                    {health.soffice_available
                      ? (health.soffice_version ?? 'detected')
                      : 'missing'}
                  </span>
                }
              />
              <Row
                label="soffice path"
                value={health.soffice_path ?? '—'}
                mono
              />
              <Row
                label="Extension bridge"
                value={
                  health.extension_bridge_online
                    ? `online (${health.extension_tool_count} tools)`
                    : 'offline'
                }
              />
              <Row
                label="Bridge URL"
                value={health.extension_bridge_url ?? '—'}
                mono
              />
              <Row label="Output dir" value={health.output_dir} mono />
              <Row label="Templates dir" value={health.templates_dir} mono />
            </div>
          </div>

          <div className="bg-ink-900 border border-ink-700 rounded-lg overflow-hidden">
            <div className="px-4 py-3 border-b border-ink-700 text-sm text-ink-200">
              Frontend :10983
            </div>
            <div className="px-4 py-1">
              <Row label="Stack" value="React + Vite + Tailwind" />
              <Row label="State" value="Zustand" />
              <Row label="Motion" value="Framer Motion" />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
