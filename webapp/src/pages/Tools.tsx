import { Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type ToolInfo } from '../lib/api'
import { useStore } from '../store'

export function Tools() {
  const { addToast } = useStore()
  const [tools, setTools] = useState<ToolInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .tools()
      .then((r) => setTools(r.tools))
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48 text-ink-500">
        <Loader2 size={18} className="animate-spin mr-2" /> Loading tools…
      </div>
    )
  }

  return (
    <div className="space-y-6 max-w-3xl">
      {tools.map((tool) => (
        <div
          key={tool.name}
          className="bg-ink-900 border border-ink-700 rounded-lg overflow-hidden"
        >
          <div className="px-4 py-3 border-b border-ink-700 flex items-center gap-3">
            <span className="font-mono text-amber-400">{tool.name}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {tool.kind}
            </span>
          </div>
          <p className="px-4 py-3 text-sm text-ink-400 border-b border-ink-800">
            {tool.description}
          </p>
          <div className="divide-y divide-ink-800">
            {tool.operations.map((op) => (
              <div key={op.name} className="px-4 py-3 flex gap-4">
                <code className="font-mono text-xs text-acid w-36 flex-shrink-0">
                  {op.name}
                </code>
                <span className="text-sm text-ink-400">{op.description}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
