import { motion } from 'framer-motion'
import { Play, Radio, Table2 } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { StudioSessionBar } from '../components/StudioSessionBar'
import { api, apiPath } from '../lib/api'
import { useStore } from '../store'

type CalcEvent = {
  type: string
  cells?: number
  message?: string
  data?: Record<string, unknown>
}

export function LiveCalcPage() {
  const { addToast } = useStore()
  const [running, setRunning] = useState(false)
  const [bridgeOk, setBridgeOk] = useState(false)
  const [events, setEvents] = useState<CalcEvent[]>([])
  const [delaySec, setDelaySec] = useState(0.08)
  const esRef = useRef<EventSource | null>(null)

  const refreshStatus = useCallback(() => {
    api
      .calcLiveStatus()
      .then((s) => setBridgeOk(s.calc_bridge_connected))
      .catch(() => setBridgeOk(false))
  }, [])

  useEffect(() => {
    refreshStatus()
    const t = window.setInterval(refreshStatus, 3000)
    return () => window.clearInterval(t)
  }, [refreshStatus])

  useEffect(() => {
    const es = new EventSource(apiPath('/api/live/calc/events'))
    esRef.current = es
    es.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as CalcEvent
        if (data.type === 'ping') return
        setEvents((prev) => [...prev.slice(-80), data])
      } catch {
        /* ignore */
      }
    }
    return () => es.close()
  }, [])

  async function launchCalc() {
    try {
      await api.launchCalc()
      addToast({
        type: 'success',
        message: 'Calc launched — install calc-bridge .oxt',
      })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }

  async function runPivotDemo() {
    if (running) return
    setRunning(true)
    setEvents([])
    try {
      const res = await api.livePivotDemo({
        typewriter_seed: true,
        launch_calc: true,
      })
      addToast({
        type: res.success ? 'success' : 'error',
        message: res.success
          ? 'Pivot demo queued — watch Calc fill cells then pivot'
          : String((res.data as { error?: string })?.error ?? 'Failed'),
      })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <StudioSessionBar compact />

      <div className="flex items-center gap-3">
        <Table2 className="text-emerald-400 w-8 h-8" />
        <div>
          <h1 className="text-2xl font-display text-ink-100">Live Calc</h1>
          <p className="text-ink-400 text-sm">
            Cell typewriter + Data Pilot pivot in the GUI (calc-bridge .oxt)
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <Radio
          className={`w-4 h-4 ${bridgeOk ? 'text-emerald-400' : 'text-ink-500'}`}
        />
        <span className={bridgeOk ? 'text-emerald-300' : 'text-amber-400'}>
          {bridgeOk ? 'Calc bridge connected' : 'Calc bridge offline'}
        </span>
      </div>

      <div className="card p-4 space-y-4">
        <label className="block text-sm text-ink-400">
          Typewriter delay (seconds per cell)
          <input
            type="number"
            step="0.01"
            min="0.02"
            max="1"
            value={delaySec}
            onChange={(e) => setDelaySec(Number(e.target.value))}
            className="mt-1 w-full bg-ink-800 border border-ink-600 rounded px-3 py-2 text-ink-100"
          />
        </label>

        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-secondary" onClick={launchCalc}>
            Launch Calc
          </button>
          <motion.button
            type="button"
            className="btn-primary flex items-center gap-2"
            onClick={runPivotDemo}
            disabled={running}
            whileTap={{ scale: 0.98 }}
          >
            <Play className="w-4 h-4" />
            {running ? 'Running…' : 'Typewriter + pivot demo'}
          </motion.button>
        </div>

        <p className="text-xs text-ink-500">
          Install:{' '}
          <code className="text-ink-300">
            dist/libreoffice-mcp-calc-bridge.oxt
          </code>
          , restart Calc, run <code className="text-ink-300">just webapp</code>.
          MCP:{' '}
          <code className="text-ink-300">
            libreoffice_calc(operation=&apos;live_pivot_demo&apos;)
          </code>
        </p>
      </div>

      <div className="card p-4">
        <h2 className="text-sm font-medium text-ink-300 mb-2">Event stream</h2>
        <ul className="text-xs font-mono text-ink-400 space-y-1 max-h-64 overflow-y-auto">
          {events.length === 0 && <li>No events yet</li>}
          {events.map((ev, i) => (
            <li key={`${ev.type}-${i}`}>
              {ev.type}
              {ev.cells != null ? ` (${ev.cells} cells)` : ''}
              {ev.message ? `: ${ev.message}` : ''}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
