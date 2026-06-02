import { motion } from 'framer-motion'
import { BookOpen, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type SkillEntry } from '../lib/api'
import { useStore } from '../store'

export function Skills() {
  const { addToast } = useStore()
  const [skills, setSkills] = useState<SkillEntry[]>([])
  const [selected, setSelected] = useState<SkillEntry | null>(null)
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .skills()
      .then(setSkills)
      .catch((e) => addToast({ type: 'error', message: e.message }))
      .finally(() => setLoading(false))
  }, [addToast])

  async function openSkill(skill: SkillEntry) {
    setSelected(skill)
    try {
      const detail = await api.skill(skill.id)
      setContent(detail.content ?? '')
    } catch (err) {
      addToast({
        type: 'error',
        message: err instanceof Error ? err.message : String(err),
      })
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-ink-500 text-sm">
        <Loader2 size={16} className="animate-spin" /> Loading skills…
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="grid lg:grid-cols-2 gap-6 max-w-5xl"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2 mb-4">
          <BookOpen size={20} className="text-amber-400" />
          Skills
        </h1>
        <p className="text-sm text-ink-500 mb-4">
          Bundled skill:// resources exposed via FastMCP SkillsDirectoryProvider
        </p>
        <ul className="space-y-2">
          {skills.map((s) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => openSkill(s)}
                className={[
                  'w-full text-left bg-ink-900 border rounded-lg px-4 py-3 transition-colors',
                  selected?.id === s.id
                    ? 'border-amber-500/50'
                    : 'border-ink-700 hover:border-ink-600',
                ].join(' ')}
              >
                <div className="text-sm font-medium text-ink-100">{s.name}</div>
                <div className="text-xs text-ink-500 mt-0.5">
                  {s.description}
                </div>
                <code className="text-[10px] text-amber-500/70 font-mono mt-1 block">
                  {s.uri}
                </code>
              </button>
            </li>
          ))}
        </ul>
      </div>
      <div className="bg-ink-950 border border-ink-800 rounded-lg p-4 min-h-[320px]">
        {selected && content ? (
          <pre className="text-xs text-ink-300 whitespace-pre-wrap font-mono leading-relaxed">
            {content}
          </pre>
        ) : (
          <p className="text-sm text-ink-600 italic">
            Select a skill to read SKILL.md
          </p>
        )}
      </div>
    </motion.div>
  )
}
