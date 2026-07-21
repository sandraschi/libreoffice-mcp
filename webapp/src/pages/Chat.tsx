import { motion } from 'framer-motion'
import { Bot, Send, Download, Trash2, Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api, type ProviderInfo } from '../lib/api'
import { useStore } from '../store'

const LS_KEY = 'libreoffice-mcp-chat-history'
const PERS_KEY = 'libreoffice-mcp-chat-personality'
const MODEL_KEY = 'libreoffice-mcp-chat-model'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  ts: string
}

const PERSONALITIES = [
  { id: 'office-expert', label: 'Office Expert', prompt: 'You are a LibreOffice expert. Guide users through document tasks with clear, actionable steps.' },
  { id: 'convert-specialist', label: 'Convert Specialist', prompt: 'You specialise in document conversion between formats. Be precise about supported formats.' },
  { id: 'quick-summarizer', label: 'Quick Summarizer', prompt: 'Keep responses brief and to the point. Use bullet points when possible.' },
  { id: 'custom', label: 'Custom', prompt: '' },
]

const EXAMPLE_GROUPS = [
  { group: 'Convert', items: ['Convert report.odt to pdf', 'Batch convert DOCX to ODT', 'Export spreadsheet to CSV'] },
  { group: 'Merge', items: ['Merge two ODT files', 'Insert template into document', 'Combine PDFs into one'] },
  { group: 'Automate', items: ['Watch folder for new DOCX and convert', 'Schedule nightly PDF export', 'Apply macro to all files in folder'] },
]

let messageSeq = 0
function nextMessageId(): string {
  messageSeq += 1
  return `msg-${messageSeq}`
}

function loadHistory(): Message[] { try { const d = localStorage.getItem(LS_KEY); return d ? JSON.parse(d) : []; } catch { return []; } }
function saveHistory(msgs: Message[]) { try { localStorage.setItem(LS_KEY, JSON.stringify(msgs.slice(-100))); } catch {} }
function loadPersonality(): string { try { return localStorage.getItem(PERS_KEY) || 'office-expert'; } catch { return 'office-expert'; } }
function loadModel(): string { try { return localStorage.getItem(MODEL_KEY) || ''; } catch { return ''; } }

function buildSystemPrompt(skillContent: string, personalityId: string): string {
  const p = PERSONALITIES.find((x) => x.id === personalityId)
  const roleText = p?.prompt || ''
  if (!skillContent && !roleText) return ''
  const parts: string[] = []
  if (skillContent) parts.push(skillContent)
  if (roleText) {
    parts.push('---')
    parts.push(`## Role\n${roleText}`)
  }
  return parts.join('\n\n')
}

export function Chat() {
  const { addToast } = useStore()
  const [messages, setMessages] = useState<Message[]>(() => loadHistory())
  const [input, setInput] = useState('')
  const [execute, setExecute] = useState(true)
  const [loading, setLoading] = useState(false)
  const [personalityId, setPersonalityId] = useState(() => loadPersonality())
  const [skillContent, setSkillContent] = useState('')
  const [skillLoaded, setSkillLoaded] = useState(false)
  const [providers, setProviders] = useState<ProviderInfo[]>([])
  const [model, setModel] = useState(() => loadModel())
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => { saveHistory(messages) }, [messages])
  useEffect(() => { localStorage.setItem(PERS_KEY, personalityId) }, [personalityId])
  useEffect(() => { localStorage.setItem(MODEL_KEY, model) }, [model])

  useEffect(() => {
    api.skills().then((skills) => {
      if (skills.length > 0) {
        const primary = skills[0]
        api.skill(primary.id).then((detail) => {
          setSkillContent(detail.content ?? '')
          setSkillLoaded(true)
        }).catch(() => setSkillLoaded(true))
      } else {
        setSkillLoaded(true)
      }
    }).catch(() => setSkillLoaded(true))

    api.llmDiscover().then((d) => setProviders(d.providers)).catch(() => {})
  }, [])

  const onlineProvider = providers.find((p) => p.online)

  async function send() {
    if (!input.trim() || loading) return
    const ts = new Date().toISOString()
    const userMsg: Message = { id: nextMessageId(), role: 'user', content: input.trim(), ts }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const systemPrompt = buildSystemPrompt(skillContent, personalityId)
      const history = messages.map((m) => ({ role: m.role, content: m.content }))
      const data = await api.chat({
        message: userMsg.content,
        system_prompt: systemPrompt || undefined,
        history,
        execute,
      })
      setMessages((m) => [...m, { id: nextMessageId(), role: 'assistant', content: data.content, ts: new Date().toISOString() }])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setMessages((m) => [...m, { id: nextMessageId(), role: 'assistant', content: `Error: ${msg}`, ts: new Date().toISOString() }])
    } finally {
      setLoading(false)
    }
  }

  const exportChat = () => {
    const text = messages.map((m) => {
      const date = new Date(m.ts)
      const time = date.toLocaleString()
      const who = m.role === 'user' ? 'You' : 'Assistant'
      return `[${time}] ${who}: ${m.content}`
    }).join('\n\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `libreoffice-chat-${new Date().toISOString().replace(/[:.]/g, '-')}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl"
      data-testid="chat-page"
    >
      <div className="mb-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-display text-ink-100">Chat</h1>
            <span className="text-xs text-amber-400 bg-amber-900/30 px-2 py-0.5 rounded border border-amber-800/50" data-testid="skill-badge">libreoffice-mcp</span>
          </div>
          <p className="text-sm text-ink-500 mt-0.5">
            Agentic LibreOffice assistant — plans and runs convert, merge, PDF merge, watch folder
          </p>
        </div>
        <div className="flex items-center gap-2" data-testid="chat-controls">
          <span className={`inline-block w-2 h-2 rounded-full ${loading ? 'bg-yellow-500 animate-pulse' : onlineProvider ? 'bg-green-500' : 'bg-gray-500'}`} title={onlineProvider ? `${onlineProvider.name} online` : 'No LLM detected'} data-testid="backend-dot" />
          <label className="flex items-center gap-2 text-xs text-ink-400">
            <input type="checkbox" checked={execute} onChange={(e) => setExecute(e.target.checked)} className="rounded border-ink-600" />
            Execute plan
          </label>
          <select value={personalityId} onChange={(e) => setPersonalityId(e.target.value)} className="rounded-md border border-ink-700 bg-ink-950 px-2 py-1 text-xs text-ink-200" data-testid="personality-select">
            {PERSONALITIES.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
          </select>
          <button type="button" onClick={exportChat} disabled={messages.length === 0} className="text-xs text-ink-400 hover:text-ink-200 p-1" data-testid="chat-export"><Download size={14} /></button>
          <button type="button" onClick={() => setMessages([])} disabled={messages.length === 0} className="text-xs text-red-400 hover:text-red-300 p-1" data-testid="chat-clear"><Trash2 size={14} /></button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4 min-h-0 border border-ink-800 rounded-lg p-4 bg-ink-900/50" data-testid="chat-messages">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-ink-600 gap-2">
            <Bot size={36} />
            <p className="text-sm text-center">
              Try: "Convert C:\docs\report.odt to pdf" or "Merge fleet-report template"
            </p>
            <div className="flex flex-wrap gap-2 mt-2" data-testid="example-prompts">
              {EXAMPLE_GROUPS.map((g) => (
                <div key={g.group} className="flex flex-wrap items-center gap-1">
                  <span className="text-[10px] font-medium text-amber-500/70 uppercase tracking-wider mr-1">{g.group}</span>
                  {g.items.map((p, i) => (
                    <button key={i} type="button" onClick={() => setInput(p)} className="text-xs bg-ink-800 hover:bg-ink-700 text-ink-400 px-2 py-0.5 rounded border border-ink-700 transition-colors">{p}</button>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[85%] px-4 py-2.5 rounded-xl text-sm whitespace-pre-wrap ${m.role === 'user' ? 'bg-amber-500/20 text-amber-100' : 'bg-ink-800 text-ink-200'}`}>
              <div className="text-[10px] text-ink-500 mb-1 font-mono">{new Date(m.ts).toLocaleTimeString()}</div>
              {m.content}
            </div>
          </div>
        ))}
        {loading && <div className="text-sm text-ink-500 animate-pulse px-2"><Loader2 className="inline animate-spin h-3 w-3 mr-1" />Thinking...</div>}
        <div ref={bottomRef} />
      </div>

      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {providers.length > 0 && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded ${onlineProvider ? 'bg-green-900/40 text-green-400' : 'bg-gray-800 text-gray-500'}`}>
            {onlineProvider ? `${onlineProvider.name}` : 'No LLM'}
          </span>
        )}
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          placeholder="Model (e.g. qwen3.5:27b)"
          className="flex-1 min-w-[120px] max-w-[200px] bg-ink-950 border border-ink-700 rounded px-2 py-0.5 text-[10px] text-ink-400 placeholder-ink-600 focus:outline-none focus:border-amber-500 font-mono"
        />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
          }}
          disabled={loading}
          placeholder="Describe a document task..."
          className="flex-1 bg-ink-950 border border-ink-700 rounded-lg px-4 py-2.5 text-sm text-ink-200 placeholder-ink-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
          data-testid="chat-input"
        />
        <button type="button" onClick={send} disabled={loading || !input.trim()} className="px-4 py-2.5 rounded-lg bg-amber-500 text-ink-950 hover:bg-amber-400 disabled:opacity-40 transition-colors" data-testid="chat-send">
          <Send size={16} />
        </button>
      </div>
    </motion.div>
  )
}