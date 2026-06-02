import { Loader2 } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { api } from '../lib/api'
import { useStore } from '../store'

export function Pack() {
  const { addToast } = useStore()
  const [pathsText, setPathsText] = useState('')
  const [title, setTitle] = useState('Fleet Artifact Pack')
  const [format, setFormat] = useState('pdf')
  const [stem, setStem] = useState('artifact-pack')
  const [busy, setBusy] = useState(false)

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    const input_paths = pathsText
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean)
    if (input_paths.length === 0) {
      addToast({ type: 'error', message: 'Add at least one markdown path' })
      return
    }
    setBusy(true)
    try {
      const result = await api.pack(input_paths, title, format, stem)
      addToast({
        type: 'success',
        message: result.data.output
          ? `Packed ${result.data.count ?? input_paths.length} files → ${result.data.output}`
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

  return (
    <div className="max-w-2xl space-y-4">
      <p className="text-sm text-ink-500">
        Combine multiple markdown files into one styled PDF via{' '}
        <code className="font-mono text-ink-400">fleet-artifact-pack.odt</code>.
        Used by{' '}
        <code className="font-mono text-ink-400">coworker_artifact_pack</code>.
      </p>
      <form
        onSubmit={onSubmit}
        className="bg-ink-900 border border-ink-700 rounded-lg p-5 space-y-4"
      >
        <label className="block text-sm">
          <span className="text-ink-400 mb-1.5 block">
            Markdown paths (one per line)
          </span>
          <textarea
            rows={8}
            value={pathsText}
            onChange={(e) => setPathsText(e.target.value)}
            placeholder="C:/Users/.../.fleet-agent/artifacts/fleet-pulse-20260530.md"
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm font-mono text-ink-200 focus:border-amber-500/50 outline-none resize-y"
          />
        </label>
        <label className="block text-sm">
          <span className="text-ink-400 mb-1.5 block">Document title</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm"
          />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block text-sm">
            <span className="text-ink-400 mb-1.5 block">Format</span>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              className="w-full bg-ink-950 border border-ink-600 rounded-md px-3 py-2 text-sm"
            >
              <option value="pdf">pdf</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="text-ink-400 mb-1.5 block">Output stem</span>
            <input
              value={stem}
              onChange={(e) => setStem(e.target.value)}
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
          Run batch pack
        </button>
      </form>
    </div>
  )
}
