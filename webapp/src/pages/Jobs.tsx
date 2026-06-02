import { CheckCircle, Loader2, RefreshCw, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type Job } from '../lib/api'
import { useStore } from '../store'

function duration(j: Job) {
  if (!j.finished) return '—'
  const ms = new Date(j.finished).getTime() - new Date(j.started).getTime()
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(1)}s`
}

function JobRow({
  job,
  active,
  onClick,
}: {
  job: Job
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'w-full text-left px-3 py-2 rounded-md transition-colors border',
        active
          ? 'bg-amber-500/10 border-amber-500/30'
          : 'bg-ink-900 border-transparent hover:border-ink-600',
      ].join(' ')}
    >
      <div className="flex items-center gap-2">
        {job.status === 'running' && (
          <Loader2 size={11} className="animate-spin text-amber-400" />
        )}
        {job.status === 'done' && (
          <CheckCircle size={11} className="text-acid" />
        )}
        {job.status === 'error' && (
          <XCircle size={11} className="text-red-400" />
        )}
        <span className="text-xs font-mono text-ink-300 truncate flex-1">
          {job.name}
        </span>
        <span className="text-xs text-ink-600">{job.id}</span>
      </div>
    </button>
  )
}

export function Jobs() {
  const { addToast, setJobs: setStoreJobs } = useStore()
  const [jobs, setJobs] = useState<Job[]>([])
  const [selected, setSelected] = useState<Job | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    api
      .jobs()
      .then((r) => {
        setJobs(r.jobs)
        setStoreJobs(r.jobs)
      })
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [addToast, setStoreJobs])

  return (
    <div className="flex gap-6 min-h-[420px]">
      <div className="w-80 flex-shrink-0 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs text-ink-500">{jobs.length} jobs</span>
          <button
            type="button"
            onClick={load}
            className="text-ink-500 hover:text-amber-400"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
        {jobs.map((j) => (
          <JobRow
            key={j.id}
            job={j}
            active={selected?.id === j.id}
            onClick={() => setSelected(j)}
          />
        ))}
        {jobs.length === 0 && !loading && (
          <div className="text-xs text-ink-600 text-center py-8">
            No jobs yet
          </div>
        )}
      </div>
      <div className="flex-1">
        {!selected ? (
          <div className="flex items-center justify-center h-48 text-ink-600 text-sm">
            Select a job
          </div>
        ) : (
          <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 space-y-3">
            <div className="font-mono text-sm text-ink-200">
              {selected.name}
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div>
                <span className="text-ink-500">Status</span>
                <div className="text-ink-300">{selected.status}</div>
              </div>
              <div>
                <span className="text-ink-500">Duration</span>
                <div className="text-ink-300">{duration(selected)}</div>
              </div>
              <div className="col-span-2">
                <span className="text-ink-500">Input</span>
                <div className="font-mono text-ink-300 break-all">
                  {selected.input}
                </div>
              </div>
            </div>
            {selected.error && (
              <pre className="text-xs text-red-400 bg-red-500/5 border border-red-500/20 rounded p-3 whitespace-pre-wrap">
                {selected.error}
              </pre>
            )}
            {selected.result && (
              <pre className="text-xs font-mono text-ink-300 bg-ink-950 border border-ink-700 rounded p-3 overflow-auto max-h-64">
                {JSON.stringify(selected.result, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
