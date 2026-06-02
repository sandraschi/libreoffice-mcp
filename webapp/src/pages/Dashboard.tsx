import { motion } from 'framer-motion'
import {
  CheckCircle,
  FileInput,
  FileStack,
  FileText,
  FolderOpen,
  GitBranch,
  Loader2,
  XCircle,
  Zap,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Health, type Job, type TemplateInfo } from '../lib/api'
import { useStore } from '../store'

function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string
  value: string
  sub: string
  accent?: boolean
}) {
  return (
    <div className="bg-ink-900 border border-ink-700 rounded-lg p-4">
      <div className="text-xs text-ink-500 uppercase tracking-wider mb-2">
        {label}
      </div>
      <div
        className={[
          'text-2xl font-display',
          accent ? 'text-amber-400' : 'text-ink-200',
        ].join(' ')}
      >
        {value}
      </div>
      <div className="text-xs text-ink-500 mt-1">{sub}</div>
    </div>
  )
}

export function Dashboard() {
  const { setHealth, addToast } = useStore()
  const [health, setLocalHealth] = useState<Health | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [templates, setTemplates] = useState<TemplateInfo[]>([])
  const [fileCount, setFileCount] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.health().then((h) => {
        setLocalHealth(h)
        setHealth(h)
      }),
      api.jobs().then((r) => setJobs(r.jobs)),
      api.templates().then((r) => setTemplates(r.templates)),
      api.output().then((r) => setFileCount(r.files.length)),
    ])
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [setHealth, addToast])

  const running = jobs.filter((j) => j.status === 'running').length
  const errors = jobs.filter((j) => j.status === 'error').length

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-ink-500">
        <Loader2 size={20} className="animate-spin mr-2" /> Loading…
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div
        className={[
          'flex items-center gap-3 px-4 py-3 rounded-lg border text-sm',
          health?.soffice_available
            ? 'bg-acid/5 border-acid/20 text-acid'
            : 'bg-red-500/5 border-red-500/20 text-red-400',
        ].join(' ')}
      >
        {health?.soffice_available ? (
          <>
            <CheckCircle size={16} />
            LibreOffice {health.soffice_version ?? ''} —{' '}
            <code className="font-mono text-xs">{health.soffice_path}</code>
          </>
        ) : (
          <>
            <XCircle size={16} />
            soffice not found — set LIBREOFFICE_MCP_SOFFICE_PATH or install
            LibreOffice 26.x
          </>
        )}
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat
          label="Templates"
          value={String(templates.length)}
          sub="bundled ODT"
        />
        <Stat label="Jobs" value={String(jobs.length)} sub="this session" />
        <Stat
          label="Running"
          value={String(running)}
          sub="active"
          accent={running > 0}
        />
        <Stat
          label="Output files"
          value={String(fileCount)}
          sub="in output dir"
        />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          {
            to: '/actions',
            icon: Zap,
            label: 'Simple Actions',
            desc: 'Status, convert, bridge discover, quick merge',
          },
          {
            to: '/workflows',
            icon: GitBranch,
            label: 'Workflows',
            desc: 'Coworker PDF flows and agentic planner',
          },
          {
            to: '/convert',
            icon: FileInput,
            label: 'Convert',
            desc: 'Queue headless format conversion',
          },
          {
            to: '/templates',
            icon: FileText,
            label: 'Templates',
            desc: 'Merge ODT placeholders → PDF',
          },
          {
            to: '/pack',
            icon: FileStack,
            label: 'Batch Pack',
            desc: 'Combine markdown files into one PDF',
          },
          {
            to: '/output',
            icon: FolderOpen,
            label: 'Output',
            desc: 'Preview PDFs and downloads',
          },
        ].map(({ to, icon: Icon, label, desc }, i) => (
          <motion.div
            key={to}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
          >
            <Link
              to={to}
              className="block bg-ink-900 border border-ink-700 hover:border-amber-500/40 hover:bg-ink-800 rounded-lg p-4 transition-colors group h-full"
            >
              <div className="flex items-center gap-3 mb-2">
                <Icon
                  size={16}
                  className="text-amber-400 group-hover:text-amber-300"
                />
                <span className="text-sm font-medium text-ink-200">
                  {label}
                </span>
              </div>
              <p className="text-xs text-ink-500">{desc}</p>
            </Link>
          </motion.div>
        ))}
      </div>

      {errors > 0 && (
        <div className="text-sm text-red-400 bg-red-500/5 border border-red-500/20 rounded-lg px-4 py-3">
          {errors} job(s) failed — see Jobs for details
        </div>
      )}
    </div>
  )
}
