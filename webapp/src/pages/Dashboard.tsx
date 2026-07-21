import { motion } from 'framer-motion'
import {
  CheckCircle,
  FileInput,
  FileStack,
  FileText,
  FolderOpen,
  GitBranch,
  Loader2,
  RefreshCw,
  XCircle,
  Zap,
  Bot,
  Cpu,
  Wifi,
  WifiOff,
} from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Health, type Job, type TemplateInfo } from '../lib/api'
import { useStore } from '../store'

function Stat({
  label, value, sub, accent, testid,
}: {
  label: string; value: string; sub: string; accent?: boolean; testid?: string
}) {
  return (
    <div className="bg-ink-900 border border-ink-700 rounded-lg p-4" data-testid={testid}>
      <div className="text-xs text-ink-500 uppercase tracking-wider mb-2">{label}</div>
      <div className={['text-2xl font-display', accent ? 'text-amber-400' : 'text-ink-200'].join(' ')}>
        {value}
      </div>
      <div className="text-xs text-ink-500 mt-1">{sub}</div>
    </div>
  )
}

async function checkHealth(): Promise<Health | null> {
  try {
    const h = await api.health()
    return h
  } catch {
    return null
  }
}

export function Dashboard() {
  const { setHealth, addToast, providers, setProviders, setGpuDetected } = useStore()
  const [localHealth, setLocalHealth] = useState<Health | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [templates, setTemplates] = useState<TemplateInfo[]>([])
  const [fileCount, setFileCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [restarting, setRestarting] = useState(false)
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const refresh = useCallback(async () => {
    const h = await checkHealth()
    setLocalHealth(h)
    if (h) setHealth(h)
    return h
  }, [setHealth])

  useEffect(() => {
    let cancelled = false
    let attempts = 0
    const intervals = [1, 2, 4, 8, 16, 30]

    async function poll() {
      const h = await refresh()
      if (cancelled) return
      if (h) {
        attempts = 0
        pollRef.current = setTimeout(poll, (intervals[intervals.length - 1] || 30) * 1000)
        return
      }
      const delay = intervals[Math.min(attempts, intervals.length - 1)] * 1000
      attempts++
      pollRef.current = setTimeout(poll, delay)
    }

    Promise.all([
      refresh(),
      api.jobs().then((r) => setJobs(r.jobs)).catch(() => {}),
      api.templates().then((r) => setTemplates(r.templates)).catch(() => {}),
      api.output().then((r) => setFileCount(r.files.length)).catch(() => {}),
      api.llmDiscover().then((d) => {
        setProviders(d.providers)
        setGpuDetected(d.gpu?.detected ?? false)
      }).catch(() => {}),
    ]).catch(() => {}).finally(() => setLoading(false))

    poll()

    return () => {
      cancelled = true
      if (pollRef.current) clearTimeout(pollRef.current)
    }
  }, [refresh, setProviders, setGpuDetected])

  useEffect(() => {
    let unlisten: (() => void) | undefined
    ;(async () => {
      try {
        // @ts-expect-error - @tauri-apps/api only resolves in Tauri WebView
        const { listen } = await import('@tauri-apps/api/event')
        unlisten = await listen('backend-status', (event: { payload: string }) => {
          if (event.payload === 'ready') refresh()
          else if (typeof event.payload === 'string' && event.payload.startsWith('error:')) {
            setLocalHealth(null)
          }
        })
      } catch {
        /* not in Tauri — polling handles it */
      }
    })()
    return () => { if (unlisten) unlisten() }
  }, [refresh])

  const restartBackend = useCallback(async () => {
    setRestarting(true)
    try {
      // @ts-expect-error - @tauri-apps/api only resolves in Tauri WebView
      const { invoke } = await import('@tauri-apps/api/core')
      await invoke('start_backend')
    } catch {
      setRestarting(false)
    }
  }, [])

  const running = jobs.filter((j) => j.status === 'running').length
  const errors = jobs.filter((j) => j.status === 'error').length
  const onlineProvider = providers.find((p) => p.online)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-ink-500">
        <Loader2 size={20} className="animate-spin mr-2" /> Loading...
      </div>
    )
  }

  return (
    <div className="space-y-6" data-testid="dashboard">
      {/* Hero section */}
      <div className="bg-gradient-to-br from-ink-900 to-ink-950 border border-ink-700 rounded-xl p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-display text-ink-100 mb-1">
              {localHealth ? `LibreOffice MCP v${localHealth.version}` : 'LibreOffice MCP'}
            </h2>
            <p className="text-sm text-ink-500 max-w-xl">
              Headless document automation for the fleet — convert, merge, batch pack, PDF operations,
              and live Writer/Calc bridge. Powered by FastMCP 3.3 and LibreOffice {localHealth?.soffice_version ?? '26.x'}.
            </p>
            <div className="flex items-center gap-4 mt-3 text-xs text-ink-500">
              <span className="flex items-center gap-1.5">
                <span className={`w-2 h-2 rounded-full ${localHealth ? 'bg-green-500' : 'bg-red-500'}`} data-testid="backend-dot" />
                {localHealth ? 'Backend connected' : 'Backend offline'}
              </span>
              {onlineProvider ? (
                <span className="flex items-center gap-1.5">
                  <Wifi size={12} className="text-green-500" />
                  {onlineProvider.name}
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <WifiOff size={12} className="text-ink-600" />
                  No LLM
                </span>
              )}
            </div>
          </div>
          {!localHealth && (
            <button
              type="button"
              onClick={restartBackend}
              disabled={restarting}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-900/30 border border-red-500/30 text-red-400 text-xs hover:bg-red-900/50 disabled:opacity-50"
            >
              <RefreshCw size={12} className={restarting ? 'animate-spin' : ''} />
              {restarting ? 'Starting...' : 'Restart Backend'}
            </button>
          )}
        </div>
      </div>

      {/* Backend status banner */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border text-sm ${localHealth?.soffice_available ? 'bg-acid/5 border-acid/20 text-acid' : 'bg-red-500/5 border-red-500/20 text-red-400'}`}>
        {localHealth?.soffice_available ? (
          <>
            <CheckCircle size={16} />
            LibreOffice {localHealth.soffice_version ?? ''} —{' '}
            <code className="font-mono text-xs">{localHealth.soffice_path}</code>
          </>
        ) : (
          <>
            <XCircle size={16} />
            soffice not found — set LIBREOFFICE_MCP_SOFFICE_PATH or install LibreOffice 26.x
          </>
        )}
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Templates" value={String(templates.length)} sub="bundled ODT" testid="kpi-templates" />
        <Stat label="Jobs" value={String(jobs.length)} sub="this session" testid="kpi-jobs" />
        <Stat label="Running" value={String(running)} sub="active" accent={running > 0} testid="kpi-running" />
        <Stat label="Output files" value={String(fileCount)} sub="in output dir" testid="kpi-output" />
      </div>

      {/* Second KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Server" value={localHealth?.version ?? '—'} sub="FastMCP 3.3" testid="kpi-server" />
        <Stat label="Tools" value={String(localHealth?.extension_tool_count ?? 0)} sub="extension bridge" testid="kpi-tools" />
        <Stat label="LLM" value={onlineProvider ? onlineProvider.name : 'none'} sub={onlineProvider ? 'online' : 'rule-based fallback'} testid="kpi-llm" />
        <Stat label="GPU" value={providers.length > 0 ? (providers[0]?.models?.length ? 'ready' : 'idle') : '—'} sub={providers.some((p) => p.online) ? 'LLM available' : 'install Ollama'} testid="kpi-gpu" />
      </div>

      {/* GPU opportunity prompt */}
      {!onlineProvider && (
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg border border-amber-500/20 bg-amber-900/10 text-amber-400 text-sm">
          <Cpu size={16} />
          <span>
            No local LLM detected.{' '}
            <a href="https://ollama.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-amber-300">
              Install Ollama
            </a>{' '}
            or{' '}
            <a href="https://lmstudio.ai" target="_blank" rel="noopener noreferrer" className="underline hover:text-amber-300">
              LM Studio
            </a>{' '}
            to unlock AI features like smart chat and enriched planning.
          </span>
        </div>
      )}

      {/* Quick-action card grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { to: '/actions', icon: Zap, label: 'Simple Actions', desc: 'Status, convert, bridge discover, quick merge' },
          { to: '/workflows', icon: GitBranch, label: 'Workflows', desc: 'Coworker PDF flows and agentic planner' },
          { to: '/convert', icon: FileInput, label: 'Convert', desc: 'Queue headless format conversion' },
          { to: '/templates', icon: FileText, label: 'Templates', desc: 'Merge ODT placeholders → PDF' },
          { to: '/pack', icon: FileStack, label: 'Batch Pack', desc: 'Combine markdown files into one PDF' },
          { to: '/output', icon: FolderOpen, label: 'Output', desc: 'Preview PDFs and downloads' },
        ].map(({ to, icon: Icon, label, desc }, i) => (
          <motion.div key={to} initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}>
            <Link to={to}
              className="block bg-ink-900 border border-ink-700 hover:border-amber-500/40 hover:bg-ink-800 rounded-lg p-4 transition-colors group h-full">
              <div className="flex items-center gap-3 mb-2">
                <Icon size={16} className="text-amber-400 group-hover:text-amber-300" />
                <span className="text-sm font-medium text-ink-200">{label}</span>
              </div>
              <p className="text-xs text-ink-500">{desc}</p>
            </Link>
          </motion.div>
        ))}
      </div>

      {/* Error summary */}
      {errors > 0 && (
        <div className="text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-4 py-3">
          {errors} job(s) failed — see Jobs for details
        </div>
      )}
    </div>
  )
}