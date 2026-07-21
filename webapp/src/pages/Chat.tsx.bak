import { motion } from 'framer-motion'
import { Bot, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

let messageSeq = 0
function nextMessageId(): string {
  messageSeq += 1
  return `msg-${messageSeq}`
}

export function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [execute, setExecute] = useState(true)
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    if (!input.trim() || loading) return
    const userMsg: Message = {
      id: nextMessageId(),
      role: 'user',
      content: input.trim(),
    }
    setMessages((m) => [...m, userMsg])
    setInput('')
    setLoading(true)
    try {
      const data = await api.chat(userMsg.content, execute)
      setMessages((m) => [
        ...m,
        { id: nextMessageId(), role: 'assistant', content: data.content },
      ])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setMessages((m) => [
        ...m,
        { id: nextMessageId(), role: 'assistant', content: `Error: ${msg}` },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-[calc(100vh-8rem)] max-w-3xl"
    >
      <div className="mb-4 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-display text-ink-100">Chat</h1>
          <p className="text-sm text-ink-500 mt-0.5">
            Agentic LibreOffice assistant — plans and runs convert, merge, PDF
            merge, watch folder
          </p>
        </div>
        <label className="flex items-center gap-2 text-xs text-ink-400">
          <input
            type="checkbox"
            checked={execute}
            onChange={(e) => setExecute(e.target.checked)}
            className="rounded border-ink-600"
          />
          Execute plan
        </label>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4 min-h-0 border border-ink-800 rounded-lg p-4 bg-ink-900/50">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-ink-600 gap-2">
            <Bot size={36} />
            <p className="text-sm text-center">
              Try: &quot;Convert C:\docs\report.odt to pdf&quot; or &quot;Merge
              fleet-report template&quot;
            </p>
          </div>
        )}
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] px-4 py-2.5 rounded-xl text-sm whitespace-pre-wrap ${
                m.role === 'user'
                  ? 'bg-amber-500/20 text-amber-100'
                  : 'bg-ink-800 text-ink-200'
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-sm text-ink-500 animate-pulse px-2">
            Planning…
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              send()
            }
          }}
          disabled={loading}
          placeholder="Describe a document task…"
          className="flex-1 bg-ink-950 border border-ink-700 rounded-lg px-4 py-2.5 text-sm text-ink-200 placeholder-ink-600 focus:outline-none focus:border-amber-500 disabled:opacity-50"
        />
        <button
          type="button"
          onClick={send}
          disabled={loading || !input.trim()}
          className="px-4 py-2.5 rounded-lg bg-amber-500 text-ink-950 hover:bg-amber-400 disabled:opacity-40 transition-colors"
        >
          <Send size={16} />
        </button>
      </div>
    </motion.div>
  )
}
