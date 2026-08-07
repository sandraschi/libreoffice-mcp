import { motion } from 'framer-motion'
import {
  ExternalLink,
  Feather,
  MonitorPlay,
  Table2,
} from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { StudioSessionBar } from '../components/StudioSessionBar'
import { api, type StudioSession } from '../lib/api'
import { familyForFile } from '../lib/studioFamily'
import { useStore } from '../store'

export function LiveStudioPage() {
  const { addToast } = useStore()
  const [session, setSession] = useState<StudioSession | null>(null)
  const [outline, setOutline] = useState(
    '# My Deck\n## Intro\n- First point\n## Next\n- More detail',
  )
  const [building, setBuilding] = useState(false)

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

  async function openInApp(
    family: 'writer' | 'calc' | 'impress',
    path?: string,
  ) {
    try {
      const result = await api.studioOpenInApp({ family, path })
      addToast({
        type: 'success',
        message: result.message ?? `${family} launched`,
      })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }

  async function buildSlides(openAfter: boolean) {
    setBuilding(true)
    try {
      const result = await api.studioOutlineToSlides({
        outline,
        open_in_impress: openAfter,
      })
      addToast({
        type: 'success',
        message: `${result.slide_count} slides → ${result.filename}`,
      })
      refresh()
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setBuilding(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl space-y-6"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <MonitorPlay size={22} className="text-amber-400" />
          Live Studio
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          Bridge status, launch LibreOffice apps, and jump to live Writer or Calc
          sessions
        </p>
      </div>

      <StudioSessionBar />
      {session?.output_dir && (
        <p className="text-xs text-ink-500 truncate -mt-2">
          Output: {session.output_dir}
        </p>
      )}

      <div className="grid sm:grid-cols-2 gap-4">
        <Link
          to="/live-write"
          className="rounded-lg border border-ink-700 bg-ink-900/60 p-4 hover:border-amber-500/40 transition-colors group"
        >
          <div className="flex items-center gap-2 text-ink-100 group-hover:text-amber-400">
            <Feather size={18} />
            <span className="font-medium">Live Write</span>
            <ExternalLink size={14} className="ml-auto opacity-50" />
          </div>
          <p className="text-xs text-ink-500 mt-2">
            Prompt → typewriter in Writer via bridge
          </p>
        </Link>
        <Link
          to="/live-calc"
          className="rounded-lg border border-ink-700 bg-ink-900/60 p-4 hover:border-amber-500/40 transition-colors group"
        >
          <div className="flex items-center gap-2 text-ink-100 group-hover:text-amber-400">
            <Table2 size={18} />
            <span className="font-medium">Live Calc</span>
            <ExternalLink size={14} className="ml-auto opacity-50" />
          </div>
          <p className="text-xs text-ink-500 mt-2">
            Cell actions and pivot demo via Calc bridge
          </p>
        </Link>
      </div>

      <div className="rounded-lg border border-ink-700 bg-ink-900/80 p-4 space-y-3">
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide">
          Launch LibreOffice
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => openInApp('writer')}
            className="px-3 py-1.5 text-sm rounded bg-amber-500/15 text-amber-400 hover:bg-amber-500/25"
          >
            Launch Writer
          </button>
          <button
            type="button"
            onClick={() => openInApp('calc')}
            className="px-3 py-1.5 text-sm rounded bg-amber-500/15 text-amber-400 hover:bg-amber-500/25"
          >
            Launch Calc
          </button>
          <button
            type="button"
            onClick={() => openInApp('impress')}
            className="px-3 py-1.5 text-sm rounded bg-amber-500/15 text-amber-400 hover:bg-amber-500/25"
          >
            Launch Impress
          </button>
        </div>
      </div>

      <div className="rounded-lg border border-ink-700 bg-ink-900/80 p-4 space-y-3">
        <p className="text-xs font-medium text-ink-400 uppercase tracking-wide">
          Outline to slides (Phase B)
        </p>
        <textarea
          value={outline}
          onChange={(e) => setOutline(e.target.value)}
          rows={8}
          className="w-full rounded border border-ink-700 bg-ink-950 px-3 py-2 text-sm text-ink-200 font-mono"
          placeholder="# Title&#10;## Slide&#10;- bullet"
        />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            disabled={building}
            onClick={() => buildSlides(false)}
            className="px-3 py-1.5 text-sm rounded bg-amber-500/15 text-amber-400 hover:bg-amber-500/25 disabled:opacity-50"
          >
            Build ODP
          </button>
          <button
            type="button"
            disabled={building}
            onClick={() => buildSlides(true)}
            className="px-3 py-1.5 text-sm rounded bg-acid/10 text-acid hover:bg-acid/20 disabled:opacity-50"
          >
            Build and open Impress
          </button>
        </div>
      </div>

      {session?.recent_outputs && session.recent_outputs.length > 0 && (
        <div className="rounded-lg border border-ink-700 bg-ink-900/80 p-4 space-y-3">
          <p className="text-xs font-medium text-ink-400 uppercase tracking-wide">
            Recent output
          </p>
          <ul className="space-y-2">
            {session.recent_outputs.slice(0, 8).map((file) => (
              <li
                key={file.name}
                className="flex flex-wrap items-center gap-2 text-sm text-ink-300"
              >
                <span className="truncate flex-1 min-w-0">{file.name}</span>
                <button
                  type="button"
                  onClick={() =>
                    openInApp(familyForFile(file.name), file.name)
                  }
                  className="text-xs text-amber-400 hover:underline shrink-0"
                >
                  Open in LO
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </motion.div>
  )
}
