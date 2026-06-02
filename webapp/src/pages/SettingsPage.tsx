import { motion } from 'framer-motion'
import { RefreshCw, Save, Settings2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type Capabilities } from '../lib/api'
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
    placeholder: 'sk-…',
    secret: true,
  },
  {
    key: 'LIBREOFFICE_MCP_OPENAI_MODEL',
    label: 'OpenAI model',
    placeholder: 'gpt-4o-mini',
  },
] as const

export function SettingsPage() {
  const { addToast } = useStore()
  const [env, setEnv] = useState<Record<string, string>>({})
  const [caps, setCaps] = useState<Capabilities | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  useEffect(() => {
    Promise.all([api.env(), api.capabilities()])
      .then(([e, c]) => {
        setEnv(
          Object.fromEntries(Object.entries(e).map(([k, v]) => [k, v ?? ''])),
        )
        setCaps(c)
      })
      .catch((err) => addToast({ type: 'error', message: err.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  async function save() {
    setSaving(true)
    try {
      await api.saveEnv(env)
      addToast({ type: 'success', message: 'Settings saved to .env' })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setSaving(false)
    }
  }

  async function testOllama() {
    setTesting(true)
    try {
      const r = await api.testLlm({
        provider: 'ollama',
        base_url: env.LIBREOFFICE_MCP_OLLAMA_BASE_URL,
        model: env.LIBREOFFICE_MCP_OLLAMA_MODEL,
      })
      addToast({ type: 'success', message: r.message ?? 'LLM OK' })
    } catch (err: unknown) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    } finally {
      setTesting(false)
    }
  }

  if (loading) {
    return <div className="text-ink-500 text-sm">Loading settings…</div>
  }

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
        >
          {saving ? (
            <RefreshCw size={14} className="animate-spin" />
          ) : (
            <Save size={14} />
          )}
          Save
        </button>
      </div>

      {caps && (
        <div className="grid grid-cols-2 gap-3 text-xs">
          {Object.entries(caps.features).map(([k, v]) => (
            <div
              key={k}
              className="bg-ink-900 border border-ink-700 rounded-md px-3 py-2 flex justify-between"
            >
              <span className="text-ink-500">{k}</span>
              <span className={v ? 'text-acid' : 'text-ink-600'}>
                {String(v)}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="space-y-4 bg-ink-900 border border-ink-700 rounded-lg p-5">
        {ENV_KEYS.map((field) => (
          <div key={field.key}>
            <label
              htmlFor={`env-${field.key}`}
              className="block text-xs text-ink-500 mb-1 font-mono"
            >
              {field.label}
            </label>
            <input
              id={`env-${field.key}`}
              type={'secret' in field && field.secret ? 'password' : 'text'}
              value={env[field.key] ?? ''}
              onChange={(e) =>
                setEnv((prev) => ({ ...prev, [field.key]: e.target.value }))
              }
              placeholder={field.placeholder}
              className="w-full bg-ink-950 border border-ink-700 rounded-md px-3 py-2 text-sm text-ink-200 font-mono focus:outline-none focus:border-amber-500"
            />
          </div>
        ))}
        <button
          type="button"
          onClick={testOllama}
          disabled={testing}
          className="text-sm text-amber-400 hover:text-amber-300 disabled:opacity-50"
        >
          {testing ? 'Testing Ollama…' : 'Test Ollama connection'}
        </button>
      </div>
    </motion.div>
  )
}
