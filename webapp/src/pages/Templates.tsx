import { Loader2 } from 'lucide-react'
import { type FormEvent, useEffect, useState } from 'react'
import { api, type TemplateInfo } from '../lib/api'
import { useStore } from '../store'

export function Templates() {
  const { addToast } = useStore()
  const [templates, setTemplates] = useState<TemplateInfo[]>([])
  const [selected, setSelected] = useState<TemplateInfo | null>(null)
  const [values, setValues] = useState<Record<string, string>>({})
  const [format, setFormat] = useState('pdf')
  const [stem, setStem] = useState('')
  const [busy, setBusy] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .templates()
      .then((r) => {
        setTemplates(r.templates)
        if (r.templates[0]) {
          setSelected(r.templates[0])
          const init: Record<string, string> = {}
          for (const p of r.templates[0].placeholders) init[p] = ''
          setValues(init)
        }
      })
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  function pickTemplate(t: TemplateInfo) {
    setSelected(t)
    const init: Record<string, string> = {}
    for (const p of t.placeholders) init[p] = values[p] ?? ''
    setValues(init)
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    if (!selected) return
    setBusy(true)
    try {
      const result = await api.merge(
        selected.name,
        values,
        format,
        stem || undefined,
      )
      addToast({
        type: 'success',
        message: result.data.output
          ? `Wrote ${result.data.output}`
          : result.message,
      })
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-ink-500">
        <Loader2 size={18} className="animate-spin mr-2" /> Loading templates…
      </div>
    )
  }

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <div className="space-y-3">
        <h2 className="text-xs text-ink-500 uppercase tracking-wider">
          Gallery
        </h2>
        {templates.map((t) => (
          <button
            key={t.name}
            type="button"
            onClick={() => pickTemplate(t)}
            className={[
              'w-full text-left p-4 rounded-lg border transition-colors',
              selected?.name === t.name
                ? 'bg-amber-500/10 border-amber-500/40'
                : 'bg-ink-900 border-ink-700 hover:border-ink-600',
            ].join(' ')}
          >
            <div className="font-mono text-sm text-ink-200">{t.name}</div>
            <div className="text-xs text-ink-500 mt-1">{t.description}</div>
            <div className="text-xs text-ink-600 mt-2 font-mono">
              {t.placeholders.join(', ') || '—'}
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <form
          onSubmit={onSubmit}
          className="bg-ink-900 border border-ink-700 rounded-lg p-5 space-y-4"
        >
          <h2 className="text-sm font-medium text-ink-200">
            Merge {selected.name}
          </h2>
          {selected.placeholders.map((key) => (
            <label key={key} className="block text-sm">
              <span className="text-ink-400 mb-1.5 block font-mono">{`{{${key}}}`}</span>
              <textarea
                rows={key.includes('BODY') || key.includes('NARRATIVE') ? 4 : 2}
                value={values[key] ?? ''}
                onChange={(e) =>
                  setValues((v) => ({ ...v, [key]: e.target.value }))
                }
                className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm text-ink-200 focus:border-amber-500/50 outline-none resize-y"
              />
            </label>
          ))}
          <div className="grid grid-cols-2 gap-3">
            <label className="block text-sm">
              <span className="text-ink-400 mb-1.5 block">Format</span>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm"
              >
                <option value="pdf">pdf</option>
                <option value="odt">odt</option>
              </select>
            </label>
            <label className="block text-sm">
              <span className="text-ink-400 mb-1.5 block">Output stem</span>
              <input
                value={stem}
                onChange={(e) => setStem(e.target.value)}
                placeholder="fleet-report"
                className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono"
              />
            </label>
          </div>
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-ink-950 font-medium text-sm px-4 py-2 rounded-md"
          >
            {busy && <Loader2 size={14} className="animate-spin" />}
            Merge & convert
          </button>
        </form>
      )}
    </div>
  )
}
