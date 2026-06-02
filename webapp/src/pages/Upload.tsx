import { motion } from 'framer-motion'
import { Upload } from 'lucide-react'
import { useState } from 'react'
import { api } from '../lib/api'
import { useStore } from '../store'

export function UploadPage() {
  const { addToast } = useStore()
  const [uploading, setUploading] = useState(false)
  const [lastPath, setLastPath] = useState<string | null>(null)
  const [docInfo, setDocInfo] = useState<Record<string, unknown> | null>(null)

  async function onFile(file: File | null) {
    if (!file) return
    setUploading(true)
    try {
      const result = await api.upload(file)
      setLastPath(result.path)
      setDocInfo(result.document as Record<string, unknown>)
      addToast({ type: 'success', message: `Uploaded ${result.name}` })
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setUploading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-xl space-y-6"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100">Upload</h1>
        <p className="text-sm text-ink-500 mt-1">
          Drop a document for convert, merge, or batch workflows — saved under
          uploads/
        </p>
      </div>

      <label className="flex flex-col items-center justify-center gap-3 border-2 border-dashed border-ink-700 rounded-xl p-12 cursor-pointer hover:border-amber-500/50 transition-colors bg-ink-900/40">
        <Upload size={32} className="text-amber-400" />
        <span className="text-sm text-ink-400">
          {uploading
            ? 'Uploading…'
            : 'Choose file (Writer, Calc, Impress, PDF, MD)'}
        </span>
        <input
          type="file"
          className="hidden"
          disabled={uploading}
          onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        />
      </label>

      {lastPath && (
        <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 space-y-2 text-sm">
          <p className="font-mono text-ink-300 break-all">{lastPath}</p>
          {docInfo && (
            <p className="text-ink-500">
              {(docInfo.family_label as string) ?? docInfo.family} · suggested:{' '}
              {(docInfo.suggested_formats as string[])?.join(', ')}
            </p>
          )}
          <p className="text-xs text-ink-600">
            Use this path on Convert, Workflows, or Chat.
          </p>
        </div>
      )}
    </motion.div>
  )
}
