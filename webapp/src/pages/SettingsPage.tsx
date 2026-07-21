import { motion } from 'framer-motion'
import { RefreshCw, Save, Settings2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type Capabilities, type ProviderInfo } from '../lib/api'
import { useStore } from '../store'

const ENV_KEYS = [
  {
    key: 'LIBREOFFICE_MCP_SOFFICE_PATH',
    label: 'soffice.exe path',
    placeholder: 'C:/Program Files/LibreOffice/program/soffice.exe',
  },
  {
    key: 'LIBREOFFICE_MCP_EXTENSION_BRIDGE_URL',
    label: 'Extension MCP URL',
    placeholder: 'http://127.0.0.1:8765/mcp',
  },
  {
    key: 'LIBREOFFICE_MCP_CENTRAL_DOCS_PATH',
    label: 'MCD path (Apps Hub)',
    placeholder: 'D:/Dev/repos/mcp-central-docs',
  },
  {
    key: 'LIBREOFFICE_MCP_OLLAMA_BASE_URL',
    label: 'Ollama base URL',
    placeholder: 'http://127.0.0.1:11434',
  },
  {
    key: 'LIBREOFFICE_MCP_OLLAMA_MODEL',
    label: 'Default Ollama model',
    placeholder: 'qwen3.5:27b',
  },
  {
    key: 'LIBREOFFICE_MCP_LMSTUDIO_BASE_URL',
    label: 'LM Studio base URL',
    placeholder: 'http://127.0.0.1:1234',
  },
  {
    key: 'LIBREOFFICE_MCP_OPENAI_API_KEY',
    label: 'OpenAI API key (optional)',
    placeholder: 'sk-...',
    secret: true,
  },
  {
    key: 'LIBREOFFICE_MCP_OPENAI_MODEL',
    label: 'OpenAI model',
    placeholder: 'gpt-4o-mini',
  },
] as const

export function SettingsPage() {
  const { addToast, providers, setProviders, gpuDetected, setGpuDetected } = useStore()
  const [env, setEnv] = useState<Record<string, string>>({})
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    Promise.all([
      api.env(),
      api.capabilities(),
      api.llmDiscover(),
    ])
      .then(([e, c, llm]) => {
        setEnv(Object.fromEntries(Object.entries(e).map(([k, v]) => [k, v ?? ''])))
        setCaps(c)
        setProviders(llm.providers)
        setGpuDetected(llm.gpu?.detected ?? false)
      })
      .catch((err) => addToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [addToast, setProviders, setGpuDetected])

  async function save() {
    setSaving(true)
    try {
      await api.saveEnv(env)
      addToast({ type: 'success', message: 'Settings saved to .env' })
    } catch (err: unknown) {
      addToast({ type: 'error', message: err instanceof Error ? err.message : String(err) })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <div className="text-ink-500 text-sm">Loading settings...</div>
  }

  const onlineProviders = providers.filter((p) => p.online)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-2xl"
    >
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
            <Settings2 size={20} className="text-amber-400" />
            Settings
          </h1>
          <p className="text-sm text-ink-500 mt-1">
            LibreOffice paths, extension bridge, local LLM, fleet docs
          </p>
        </div>
        <button
          type="button"
          onClick={save}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-amber-500 text-ink-950 text-sm font-medium hover:bg-amber-400 disabled:opacity-50"
          data-testid="settings-save"
        >
          {saving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
          Save
        </button>
      </div>

      {/* Provider status */}
      <div className="bg-ink-900 border border-ink-700 rounded-lg p-4 space-y-2" data-testid="settings-providers">
        <h3 className="text-xs font-medium text-ink-400 uppercase tracking-wider">LLM Providers</h3>
        {providers.length === 0 ? (
          <p className="text-xs text-ink-600">No providers discovered.</p>
        ) : (
          providers.map((p) => (
            <div key={p.id} className="flex items-center justify-between text-sm" data-testid={`provider-${p.id}`}>
              <span className="text-ink-300">{p.name}</span>
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full ${p.online ? 'bg-green-500' : 'bg-ink-600'}`} />
                <span className={p.online ? 'text-green-400 text-xs' : 'text-ink-500 text-xs'}>
                  {p.online ? `${p.models.length} models` : 'offline'}
                </span>
              </div>
            </div>
          ))
        )}
        <div className="flex items-center justify-between text-sm pt-1 border-t border-ink-700">
          <span className="text-ink-300">GPU</span>
          <span className="text-xs" data-testid="settings-gpu">
            {gpuDetected ? (
              <span className="text-green-400">GPU detected</span>
            ) : (
              <span className="text-ink-500">Not detected</span>
            )}
          </span>
        </div>
      </div>

      {caps && (
        <div className="grid grid-cols-2 gap-3 text-xs" data-testid="settings-features">
          {Object.entries(caps.features).map(([k, v]) => (
            <div key={k} className="bg-ink-900 border border-ink-700 rounded-md px-3 py-2 flex justify-between">
              <span className="text-ink-500">{k}</span>
              <span className={v ? 'text-acid' : 'text-ink-600'}>{String(v)}</span>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-4 bg-ink-900 border border-ink-700 rounded-lg p-5">
        {ENV_KEYS.map((field, idx) => (
          <div key={field.key}>
            <label htmlFor={`env-${field.key}`} className="block text-xs text-ink-500 mb-1 font-mono">
              {field.label}
            </label>
            <input
              id={`env-${field.key}`}
              type={'secret' in field && field.secret ? 'password' : 'text'}
              value={env[field.key] ?? ''}
              onChange={(e) => setEnv((prev) => ({ ...prev, [field.key]: e.target.value }))}
              placeholder={field.placeholder}
              className="w-full bg-ink-950 border border-ink-700 rounded-md px-3 py-2 text-sm text-ink-200 font-mono focus:outline-none focus:border-amber-500"
              data-testid={`env-${field.key}`}
            />
          </div>
        ))}
        {onlineProviders.length > 0 && (
          <div className="text-xs text-green-400/80">
            {onlineProviders.map((p) => `${p.name} connected (${p.models.length} models)`).join(', ')}
          </div>
        )}
      </div>
    </motion.div>
  )
}