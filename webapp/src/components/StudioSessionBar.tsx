import { MonitorPlay, Radio } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type StudioSession } from '../lib/api'

function StatusPill({ label, ok }: { label: string; ok: boolean }) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs',
        ok ? 'bg-acid/10 text-acid' : 'bg-ink-800 text-ink-400',
      ].join(' ')}
    >
      <Radio size={12} />
      {label} {ok ? 'ready' : 'offline'}
    </span>
  )
}

type Props = {
  compact?: boolean
}

export function StudioSessionBar({ compact = false }: Props) {
  const [session, setSession] = useState<StudioSession | null>(null)

  const refresh = useCallback(() => {
    api
      .studioSession()
      .then(setSession)
      .catch(() => setSession(null))
  }, [])

  useEffect(() => {
    refresh()
    const t = window.setInterval(refresh, 5000)
    return () => window.clearInterval(t)
  }, [refresh])

  return (
    <div
      className={[
        'rounded-lg border border-ink-700 bg-ink-900/80 flex flex-wrap items-center gap-2',
        compact ? 'px-3 py-2' : 'p-4',
      ].join(' ')}
    >
      {!compact && (
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide w-full sm:w-auto">
          Live session
        </p>
      )}
      <StatusPill label="soffice" ok={!!session?.soffice_available} />
      <StatusPill
        label="writer bridge"
        ok={!!session?.writer_bridge_connected}
      />
      <StatusPill label="calc bridge" ok={!!session?.calc_bridge_connected} />
      <Link
        to="/studio"
        className="ml-auto inline-flex items-center gap-1 text-xs text-amber-400 hover:text-amber-300"
      >
        <MonitorPlay size={14} />
        Studio
      </Link>
    </div>
  )
}
