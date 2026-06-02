import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type HelpInfo } from '../lib/api'
import { useStore } from '../store'

export function Help() {
  const { addToast } = useStore()
  const [help, setHelp] = useState<HelpInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .help()
      .then(setHelp)
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-ink-500">
        <Loader2 size={18} className="animate-spin mr-2" /> Loading…
      </div>
    )
  }

  if (!help) return null

  return (
    <div className="max-w-2xl space-y-6 text-sm">
      <div className="bg-ink-900 border border-ink-700 rounded-lg p-5">
        <h2 className="font-display text-amber-400 text-lg mb-2">
          {help.title}
        </h2>
        <p className="text-ink-400">
          Version {help.version} — FOSS office layer for Fritz coworker PDF
          flows.
        </p>
      </div>

      <section>
        <h3 className="text-xs text-ink-500 uppercase tracking-wider mb-2">
          Ports
        </h3>
        <ul className="font-mono text-xs text-ink-300 space-y-1">
          {Object.entries(help.ports).map(([k, v]) => (
            <li key={k}>
              {k}: {v}
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="text-xs text-ink-500 uppercase tracking-wider mb-2">
          Host
        </h3>
        <p className="text-ink-400 mb-2">{help.host.soffice}</p>
        <p className="font-mono text-xs text-ink-500">
          {help.host.env.join(', ')}
        </p>
      </section>

      <section>
        <h3 className="text-xs text-ink-500 uppercase tracking-wider mb-2">
          Coworker flows
        </h3>
        <ul className="list-disc list-inside text-ink-400 space-y-1">
          {help.coworker_flows.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </section>

      <section>
        <h3 className="text-xs text-ink-500 uppercase tracking-wider mb-2">
          Templates
        </h3>
        <div className="flex flex-wrap gap-2">
          {help.templates.map((t) => (
            <span
              key={t}
              className="font-mono text-xs px-2 py-1 rounded bg-ink-800 border border-ink-700 text-ink-300"
            >
              {t}
            </span>
          ))}
        </div>
      </section>

      <p className="text-xs text-ink-600">
        Docs: mcp-central-docs/projects/libreoffice-mcp — launch via
        starts/libreoffice-mcp-start.bat
      </p>
    </div>
  )
}
