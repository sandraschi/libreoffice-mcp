import { X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type HelpInfo } from '../lib/api'
import { useStore } from '../store'

export function HelpModal() {
  const { helpOpen, setHelpOpen } = useStore()
  const [help, setHelp] = useState<HelpInfo | null>(null)

  useEffect(() => {
    if (!helpOpen) return
    api
      .help()
      .then(setHelp)
      .catch(() => setHelp(null))
  }, [helpOpen])

  if (!helpOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-ink-900 border border-ink-700 rounded-xl max-w-lg w-full max-h-[80vh] overflow-y-auto shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-ink-700">
          <h2 className="font-display text-amber-400">Help</h2>
          <button
            type="button"
            onClick={() => setHelpOpen(false)}
            className="text-ink-500 hover:text-ink-200"
          >
            <X size={18} />
          </button>
        </div>
        <div className="px-5 py-4 text-sm text-ink-400 space-y-3">
          {help ? (
            <>
              <p>
                {help.title} v{help.version}
              </p>
              <p>
                Backend :{help.ports?.backend ?? 10981} · Dashboard :
                {help.ports?.frontend ?? 10983} · Extension bridge :8765
              </p>
              <p className="font-mono text-xs text-ink-500">
                {help.host.env.join(' · ')}
              </p>
            </>
          ) : (
            <p>Loading…</p>
          )}
        </div>
      </div>
    </div>
  )
}
