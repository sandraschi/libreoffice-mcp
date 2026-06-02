import { ExternalLink, RefreshCw } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type OutputFile } from '../lib/api'
import { useStore } from '../store'

export function Output() {
  const { addToast } = useStore()
  const [files, setFiles] = useState<OutputFile[]>([])
  const [outputDir, setOutputDir] = useState('')
  const [preview, setPreview] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = () => {
    setLoading(true)
    api
      .output()
      .then((r) => {
        setFiles(r.files)
        setOutputDir(r.output_dir)
      })
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [addToast])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <p className="text-xs font-mono text-ink-500 truncate flex-1">
          {outputDir || '—'}
        </p>
        <button
          type="button"
          onClick={load}
          className="text-ink-500 hover:text-amber-400"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
        </button>
      </div>

      <div className="bg-ink-900 border border-ink-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-ink-700 text-left text-xs text-ink-500 uppercase">
              <th className="px-4 py-3">File</th>
              <th className="px-4 py-3">Size</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {files.length === 0 ? (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-ink-600">
                  No output files yet
                </td>
              </tr>
            ) : (
              files.map((f) => (
                <tr
                  key={f.path}
                  className="border-b border-ink-800/80 last:border-0"
                >
                  <td className="px-4 py-2.5 font-mono text-ink-300">
                    {f.name}
                  </td>
                  <td className="px-4 py-2.5 text-ink-500">
                    {Math.round(f.size_bytes / 1024)} KB
                  </td>
                  <td className="px-4 py-2.5 text-right space-x-2">
                    {f.previewable && (
                      <button
                        type="button"
                        onClick={() => setPreview(f.name)}
                        className="text-amber-400 hover:text-amber-300 text-xs"
                      >
                        Preview
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() =>
                        api
                          .revealOutput(f.name)
                          .then(() =>
                            addToast({
                              type: 'success',
                              message: `Opened ${f.name} in Explorer`,
                            }),
                          )
                          .catch((e) =>
                            addToast({ type: 'error', message: e.message }),
                          )
                      }
                      className="text-ink-400 hover:text-ink-200 text-xs"
                    >
                      Reveal
                    </button>
                    <a
                      href={api.previewUrl(f.name)}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-ink-400 hover:text-ink-200 text-xs"
                    >
                      Open <ExternalLink size={11} />
                    </a>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {preview && (
        <div className="bg-ink-900 border border-ink-700 rounded-lg p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-mono text-ink-300">{preview}</h2>
            <button
              type="button"
              onClick={() => setPreview(null)}
              className="text-xs text-ink-500 hover:text-ink-300"
            >
              Close
            </button>
          </div>
          <iframe
            title="preview"
            src={api.previewUrl(preview)}
            className="w-full h-[70vh] rounded-md border border-ink-700 bg-white"
          />
        </div>
      )}
    </div>
  )
}
