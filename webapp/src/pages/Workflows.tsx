import { motion } from 'framer-motion'
import { Bot, Cpu, GitBranch, Loader2, Play, Sparkles } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import {
  type AgenticPlan,
  api,
  type WorkflowDef,
  type WorkflowPlaceholder,
} from '../lib/api'
import { useStore } from '../store'

function placeholderDefaults(
  fields: WorkflowPlaceholder[],
  today: string,
): Record<string, string> {
  const out: Record<string, string> = {}
  for (const f of fields) {
    if (f.default_from === 'today') out[f.key] = today
    else if (f.default) out[f.key] = f.default
    else out[f.key] = ''
  }
  return out
}

function WorkflowPanel({
  workflow,
  today,
  onRun,
  busy,
}: {
  workflow: WorkflowDef
  today: string
  onRun: (id: string, params: Record<string, unknown>) => void
  busy: string | null
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    workflow.placeholders
      ? placeholderDefaults(workflow.placeholders, today)
      : {},
  )
  const [pathsText, setPathsText] = useState('')
  const [title, setTitle] = useState('Document Pack')
  const [stem, setStem] = useState(workflow.output_stem_default ?? '')
  const [bridgeTool, setBridgeTool] = useState('')
  const [bridgeArgs, setBridgeArgs] = useState('{}')

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (workflow.operation === 'batch_pack') {
      const input_paths = pathsText
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean)
      onRun(workflow.id, {
        input_paths,
        title,
        output_stem: stem,
        output_format: 'pdf',
      })
      return
    }
    if (workflow.operation === 'bridge_call') {
      onRun(workflow.id, {
        bridge_tool: bridgeTool,
        bridge_arguments: bridgeArgs,
      })
      return
    }
    onRun(workflow.id, {
      placeholders: values,
      output_stem: stem || workflow.output_stem_default,
      output_format: 'pdf',
    })
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-ink-900 border border-ink-700 rounded-lg p-5 space-y-3"
    >
      <div>
        <h3 className="text-sm font-medium text-ink-100">{workflow.label}</h3>
        <p className="text-xs text-ink-500 mt-0.5">{workflow.description}</p>
        {workflow.coworker_flow && (
          <code className="text-[10px] text-amber-500/80 font-mono mt-1 block">
            {workflow.coworker_flow}
          </code>
        )}
      </div>

      {workflow.placeholders?.map((field) => (
        <label
          key={field.key}
          htmlFor={`wf-${workflow.id}-${field.key}`}
          className="block text-xs"
        >
          <span className="text-ink-400 mb-1 block">{field.label}</span>
          {field.multiline ? (
            <textarea
              id={`wf-${workflow.id}-${field.key}`}
              rows={3}
              value={values[field.key] ?? ''}
              onChange={(e) =>
                setValues((v) => ({ ...v, [field.key]: e.target.value }))
              }
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono"
            />
          ) : (
            <input
              id={`wf-${workflow.id}-${field.key}`}
              value={values[field.key] ?? ''}
              onChange={(e) =>
                setValues((v) => ({ ...v, [field.key]: e.target.value }))
              }
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm"
            />
          )}
        </label>
      ))}

      {workflow.operation === 'batch_pack' && (
        <>
          <label htmlFor={`wf-${workflow.id}-paths`} className="block text-xs">
            <span className="text-ink-400 mb-1 block">Markdown paths</span>
            <textarea
              id={`wf-${workflow.id}-paths`}
              rows={5}
              value={pathsText}
              onChange={(e) => setPathsText(e.target.value)}
              placeholder="One absolute path per line"
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs font-mono"
            />
          </label>
          <label htmlFor={`wf-${workflow.id}-title`} className="block text-xs">
            <span className="text-ink-400 mb-1 block">Title</span>
            <input
              id={`wf-${workflow.id}-title`}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm"
            />
          </label>
        </>
      )}

      {workflow.operation === 'bridge_call' && (
        <>
          <label htmlFor={`wf-${workflow.id}-tool`} className="block text-xs">
            <span className="text-ink-400 mb-1 block">Bridge tool</span>
            <input
              id={`wf-${workflow.id}-tool`}
              value={bridgeTool}
              onChange={(e) => setBridgeTool(e.target.value)}
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono"
            />
          </label>
          <label htmlFor={`wf-${workflow.id}-args`} className="block text-xs">
            <span className="text-ink-400 mb-1 block">Arguments (JSON)</span>
            <textarea
              id={`wf-${workflow.id}-args`}
              rows={3}
              value={bridgeArgs}
              onChange={(e) => setBridgeArgs(e.target.value)}
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs font-mono"
            />
          </label>
        </>
      )}

      {workflow.template && (
        <label htmlFor={`wf-${workflow.id}-stem`} className="block text-xs">
          <span className="text-ink-400 mb-1 block">Output stem</span>
          <input
            id={`wf-${workflow.id}-stem`}
            value={stem}
            onChange={(e) => setStem(e.target.value)}
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono"
          />
        </label>
      )}

      <button
        type="submit"
        disabled={busy === workflow.id}
        className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-ink-950 text-sm font-medium px-4 py-2 rounded-md"
      >
        {busy === workflow.id ? (
          <Loader2 size={14} className="animate-spin" />
        ) : (
          <Play size={14} />
        )}
        Run workflow
      </button>
    </form>
  )
}

export function Workflows() {
  const { addToast } = useStore()
  const [workflows, setWorkflows] = useState<WorkflowDef[]>([])
  const [today, setToday] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState<string | null>(null)
  const [goal, setGoal] = useState('')
  const [plan, setPlan] = useState<AgenticPlan | null>(null)
  const [planLoading, setPlanLoading] = useState(false)

  useEffect(() => {
    api
      .workflowsCatalog()
      .then((r) => {
        setWorkflows(r.workflows)
        setToday(r.defaults.today)
      })
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  async function runWorkflow(id: string, params: Record<string, unknown>) {
    setBusy(id)
    try {
      const result = await api.runWorkflow(id, params)
      addToast({
        type: 'success',
        message: result.message ?? `Workflow ${id} done`,
      })
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setBusy(null)
    }
  }

  async function planGoal(execute: boolean) {
    if (!goal.trim()) return
    setPlanLoading(true)
    setPlan(null)
    try {
      const result = await api.agentic(goal.trim(), {
        execute,
        use_llm: !execute,
      })
      setPlan(result)
      if (execute && result.success) {
        addToast({ type: 'success', message: result.message ?? 'Executed' })
      }
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setPlanLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading workflows…
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8 max-w-4xl"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <GitBranch size={20} className="text-amber-400" />
          Workflows
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          Coworker PDF flows, batch packs, and extension bridge — multi-step
          agentic actions
        </p>
      </div>

      <section className="bg-ink-900/80 border border-ink-700 rounded-lg p-5 space-y-4">
        <div className="flex items-center gap-2 text-amber-400">
          <Sparkles size={16} />
          <h2 className="text-sm font-medium text-ink-100">Agentic planner</h2>
        </div>
        <p className="text-xs text-ink-500">
          Describe a document task in plain language — get a plan or run the
          first matching step.
        </p>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          rows={3}
          placeholder='e.g. "Convert C:/reports/weekly.md to PDF" or "Run weekly fleet report coworker flow"'
          className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm text-ink-200"
        />
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => planGoal(false)}
            disabled={planLoading || !goal.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md border border-ink-600 text-sm text-ink-200 hover:border-amber-500 disabled:opacity-50"
          >
            <Bot size={14} />
            Plan only
          </button>
          <button
            type="button"
            onClick={() => planGoal(true)}
            disabled={planLoading || !goal.trim()}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-amber-500 text-ink-950 text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
          >
            {planLoading ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Cpu size={14} />
            )}
            Plan &amp; execute
          </button>
        </div>
        {plan && (
          <pre className="text-xs font-mono bg-ink-950 border border-ink-800 rounded-lg p-4 text-ink-300 whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(plan, null, 2)}
          </pre>
        )}
      </section>

      <div className="space-y-4">
        <h2 className="text-xs text-ink-500 uppercase tracking-wider">
          Coworker &amp; batch workflows
        </h2>
        {workflows.map((wf) => (
          <WorkflowPanel
            key={wf.id}
            workflow={wf}
            today={today}
            onRun={runWorkflow}
            busy={busy}
          />
        ))}
      </div>
    </motion.div>
  )
}
