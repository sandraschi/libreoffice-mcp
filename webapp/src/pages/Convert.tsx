import { Loader2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { api } from '../lib/api'
import { useStore } from '../store'

export function Convert() {
  const { addToast } = useStore()
  const [inputPath, setInputPath] = useState('')
  const [format, setFormat] = useState('pdf')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      const result = await api.convert(inputPath.trim(), format)
      addToast({ type: 'success', message: result.message })
      setInputPath('')
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <p className="text-sm text-ink-500">
        Headless{' '}
        <code className="font-mono text-ink-400">soffice --convert-to</code>.
        Markdown inputs render to HTML before PDF export.
      </p>
      <form
        onSubmit={onSubmit}
        className="bg-ink-900 border border-ink-700 rounded-lg p-5 space-y-4"
      >
        <label className="block text-sm">
          <span className="text-ink-400 mb-1.5 block">
            Input path (absolute)
          </span>
          <input
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            placeholder="C:/Users/.../fleet-pulse-20260530.md"
            required
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono text-ink-200 focus:border-amber-500/50 outline-none"
          />
        </label>
        <label className="block text-sm">
          <span className="text-ink-400 mb-1.5 block">Output format</span>
          <select
            value={format}
            onChange={(e) => setFormat(e.target.value)}
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm text-ink-200 focus:border-amber-500/50 outline-none"
          >
            <option value="pdf">pdf</option>
            <option value="odt">odt</option>
            <option value="docx">docx</option>
            <option value="html">html</option>
          </select>
        </label>
        <button
          type="submit"
          disabled={busy || !inputPath.trim()}
          className="inline-flex items-center gap-2 bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-ink-950 font-medium text-sm px-4 py-2 rounded-md transition-colors"
        >
          {busy && <Loader2 size={14} className="animate-spin" />}
          Queue convert job
        </button>
      </form>
    </div>
  )
}
