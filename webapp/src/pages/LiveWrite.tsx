import { motion } from 'framer-motion'
import { Feather, Play, Radio } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { StudioSessionBar } from '../components/StudioSessionBar'
import { api, apiPath } from '../lib/api'
import { useStore } from '../store'

type LiveEvent = {
  type: string
  text?: string
  message?: string
  preview?: string
  progress?: number
  typed_chars?: number
  mode?: string
  output?: string
}

export function LiveWritePage() {
  const { health, addToast } = useStore()
  const [prompt, setPrompt] = useState(
    'Write a short story about butterflies in a summer garden',
  )
  const [wpm, setWpm] = useState(180)
  const [running, setRunning] = useState(false)
  const [bridgeOk, setBridgeOk] = useState(false)
  const [events, setEvents] = useState<LiveEvent[]>([])
  const [streamText, setStreamText] = useState('')
  const esRef = useRef<EventSource | null>(null)

  const refreshStatus = useCallback(() => {
    api
      .liveStatus()
      .then((s) => setBridgeOk(s.writer_bridge_connected))
      .catch(() => setBridgeOk(false))
  }, [])

  useEffect(() => {
    refreshStatus()
    const t = window.setInterval(refreshStatus, 3000)
    return () => window.clearInterval(t)
  }, [refreshStatus])

  useEffect(() => {
    const es = new EventSource(apiPath('/api/live/events'))
    esRef.current = es
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as LiveEvent
        if (data.type === 'ping') return
        setEvents((prev) => [...prev.slice(-80), data])
        if (data.type === 'chunk' && data.text) {
          setStreamText((t) => t + data.text)
        }
        if (data.type === 'start') {
          setStreamText('')
        }
      } catch {
        /* ignore */
      }
    }
    return () => es.close()
  }, [])

  async function launchWriter() {
    try {
      await api.launchWriter()
      addToast({
        type: 'success',
        message: 'Writer launched — run the bridge macro',
      })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }

  async function startLiveWrite() {
    if (!prompt.trim() || running) return
    setRunning(true)
    setEvents([])
    setStreamText('')
    try {
      const result = await api.liveWrite({
        prompt: prompt.trim(),
        wpm,
        launch_writer: true,
      })
      if (result.success) {
        addToast({
          type: 'success',
          message: `Done (${result.data?.mode ?? 'live'})`,
        })
      } else {
        addToast({
          type: 'error',
          message: String(result.data?.error ?? 'Live write failed'),
        })
      }
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setRunning(false)
      refreshStatus()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl space-y-6"
    >
      <StudioSessionBar compact />

      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <Feather size={22} className="text-amber-400" />
          Live Write
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          Say what to write — watch LibreOffice Writer type it live (blender-mcp
          hands-in / hands-out pattern)
        </p>
      </div>

      <div className="rounded-lg border border-ink-700 bg-ink-900/80 p-4 space-y-3">
        <div className="flex flex-wrap items-center gap-3 text-xs">
          <span
            className={[
              'inline-flex items-center gap-1.5 px-2 py-1 rounded',
              bridgeOk ? 'bg-acid/10 text-acid' : 'bg-ink-800 text-ink-400',
            ].join(' ')}
          >
            <Radio size={12} />
            Writer bridge {bridgeOk ? 'connected' : 'offline'}
          </span>
          <span className="text-ink-500">
            LO {health?.soffice_available ? 'ready' : 'missing'}
          </span>
        </div>
        <ol className="text-xs text-ink-400 list-decimal list-inside space-y-1">
          <li>
            Install{' '}
            <code className="text-ink-300">
              dist/libreoffice-mcp-bridge.oxt
            </code>{' '}
            (see EXTENSION_BRIDGE.md)
          </li>
          <li>
            Start backend: <code className="text-ink-300">just webapp</code>
          </li>
          <li>
            <button
              type="button"
              onClick={launchWriter}
              className="text-amber-400 hover:underline"
            >
              Launch Writer
            </button>{' '}
            — bridge auto-starts with LibreOffice
          </li>
          <li>Enter a prompt → Watch it write</li>
        </ol>
      </div>

      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        className="w-full rounded-lg border border-ink-700 bg-ink-950 px-3 py-2 text-sm text-ink-100"
        placeholder="Write a short story about butterflies…"
      />

      <div className="flex flex-wrap items-center gap-4">
        <label className="text-xs text-ink-400 flex items-center gap-2">
          WPM
          <input
            type="number"
            min={40}
            max={400}
            value={wpm}
            onChange={(e) => setWpm(Number(e.target.value))}
            className="w-20 rounded border border-ink-700 bg-ink-950 px-2 py-1 text-ink-100"
          />
        </label>
        <button
          type="button"
          disabled={running}
          onClick={startLiveWrite}
          className="inline-flex items-center gap-2 rounded-md bg-amber-500/20 text-amber-400 border border-amber-500/40 px-4 py-2 text-sm hover:bg-amber-500/30 disabled:opacity-50"
        >
          <Play size={16} />
          {running ? 'Writing…' : 'Watch it write'}
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        <div className="rounded-lg border border-ink-700 bg-ink-950 p-4 min-h-[200px]">
          <h2 className="text-xs font-mono text-ink-500 mb-2">
            Typewriter stream
          </h2>
          <p className="text-sm text-ink-200 whitespace-pre-wrap font-serif leading-relaxed">
            {streamText || (
              <span className="text-ink-600 italic">
                Chunks appear here as Writer receives them…
              </span>
            )}
          </p>
        </div>
        <div className="rounded-lg border border-ink-700 bg-ink-950 p-4 max-h-[280px] overflow-y-auto">
          <h2 className="text-xs font-mono text-ink-500 mb-2">Events</h2>
          <ul className="space-y-1 text-xs font-mono text-ink-400">
            {events.map((ev, i) => (
              <li key={`${ev.type}-${i}`}>
                <span className="text-amber-500">{ev.type}</span>
                {ev.message ? `: ${ev.message}` : ''}
                {ev.preview ? `: ${ev.preview}` : ''}
                {ev.text ? `: ${ev.text.slice(0, 40)}` : ''}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </motion.div>
  )
}
