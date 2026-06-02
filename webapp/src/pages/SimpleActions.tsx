import { motion } from 'framer-motion'
import {
  Activity,
  FileInput,
  FileText,
  Loader2,
  Play,
  Plug,
  Zap,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import {
  type ActionCatalog,
  api,
  type SimpleActionDef,
  type TemplateInfo,
} from '../lib/api'
import { useStore } from '../store'

const ICONS: Record<string, typeof Zap> = {
  status: Activity,
  bridge_discover: Plug,
  list_templates: FileText,
  convert: FileInput,
  quick_merge: FileText,
}

function ActionCard({
  action,
  templates,
  onRun,
  busy,
}: {
  action: SimpleActionDef
  templates: TemplateInfo[]
  onRun: (id: string, params: Record<string, unknown>) => void
  busy: string | null
}) {
  const Icon = ICONS[action.id] ?? Zap
  const [params, setParams] = useState<Record<string, string>>({
    input_path: '',
    output_format: 'pdf',
    template: templates[0]?.name ?? 'fleet-report.odt',
    output_stem: '',
  })
  const [placeholders, setPlaceholders] = useState<Record<string, string>>({})

  const selectedTemplate = templates.find((t) => t.name === params.template)

  useEffect(() => {
    if (!selectedTemplate) return
    const init: Record<string, string> = {}
    for (const p of selectedTemplate.placeholders)
      init[p] = placeholders[p] ?? ''
    setPlaceholders(init)
  }, [selectedTemplate?.name])

  function submit() {
    const payload: Record<string, unknown> = { ...params }
    if (action.dynamic_placeholders) {
      payload.placeholders = placeholders
    }
    if (action.id === 'convert') {
      payload.queue_job = true
    }
    onRun(action.id, payload)
  }

  return (
    <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 space-y-3">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-md bg-amber-500/10 text-amber-400">
          <Icon size={18} />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-ink-100">{action.label}</h3>
          <p className="text-xs text-ink-500 mt-0.5">{action.description}</p>
        </div>
      </div>

      {action.id === 'convert' && (
        <div className="space-y-2">
          <input
            value={params.input_path}
            onChange={(e) =>
              setParams((p) => ({ ...p, input_path: e.target.value }))
            }
            placeholder="C:/path/to/document.md"
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs font-mono"
          />
          <select
            value={params.output_format}
            onChange={(e) =>
              setParams((p) => ({ ...p, output_format: e.target.value }))
            }
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs"
          >
            <option value="pdf">pdf</option>
            <option value="odt">odt</option>
            <option value="docx">docx</option>
            <option value="html">html</option>
          </select>
        </div>
      )}

      {action.id === 'quick_merge' && (
        <div className="space-y-2">
          <select
            value={params.template}
            onChange={(e) =>
              setParams((p) => ({ ...p, template: e.target.value }))
            }
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs"
          >
            {templates.map((t) => (
              <option key={t.name} value={t.name}>
                {t.name}
              </option>
            ))}
          </select>
          {selectedTemplate?.placeholders.map((key) => (
            <textarea
              key={key}
              rows={2}
              value={placeholders[key] ?? ''}
              onChange={(e) =>
                setPlaceholders((prev) => ({ ...prev, [key]: e.target.value }))
              }
              placeholder={key}
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs font-mono"
            />
          ))}
          <input
            value={params.output_stem}
            onChange={(e) =>
              setParams((p) => ({ ...p, output_stem: e.target.value }))
            }
            placeholder="output stem (optional)"
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-xs font-mono"
          />
        </div>
      )}

      <button
        type="button"
        onClick={submit}
        disabled={busy === action.id}
        className="inline-flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-md bg-amber-500 text-ink-950 hover:bg-amber-400 disabled:opacity-50"
      >
        {busy === action.id ? (
          <Loader2 size={12} className="animate-spin" />
        ) : (
          <Play size={12} />
        )}
        Run
      </button>
    </div>
  )
}

export function SimpleActions() {
  const { addToast } = useStore()
  const [catalog, setCatalog] = useState<ActionCatalog | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .actionsCatalog()
      .then(setCatalog)
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  async function runAction(id: string, params: Record<string, unknown>) {
    setBusy(id)
    setLastResult(null)
    try {
      const result = await api.runAction(id, params)
      const text = result.message
        ? result.message
        : JSON.stringify(result.data ?? result, null, 2)
      setLastResult(text)
      addToast({
        type: 'success',
        message: result.message ?? `${id} completed`,
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

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading actions…
      </div>
    )
  }

  const actions = catalog?.simple_actions ?? []
  const templates = catalog?.templates ?? []

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-4xl"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <Zap size={20} className="text-amber-400" />
          Simple Actions
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          One-shot LibreOffice ops — status, convert, bridge discover, quick
          merge
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {actions.map((action) => (
          <ActionCard
            key={action.id}
            action={action}
            templates={templates}
            onRun={runAction}
            busy={busy}
          />
        ))}
      </div>

      {lastResult && (
        <pre className="text-xs font-mono bg-ink-950 border border-ink-800 rounded-lg p-4 text-ink-300 whitespace-pre-wrap overflow-x-auto">
          {lastResult}
        </pre>
      )}
    </motion.div>
  )
}
