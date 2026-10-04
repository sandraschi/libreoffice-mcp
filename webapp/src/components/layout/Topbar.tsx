import { AnimatePresence, motion } from 'framer-motion'
import { HelpCircle, Moon, Sun, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { type Toast, useStore } from '../../store'

// EXPERIMENTAL light mode (invert hack). Not fleet standard - see index.css.
// Toggling `.dark` off the root flips the invert filter; persisted so the
// choice survives reloads. Delete this + the CSS block to revert.
const THEME_KEY = 'libreoffice-light-mode'

function useExperimentalTheme() {
  const [light, setLight] = useState(() => {
    try {
      return localStorage.getItem(THEME_KEY) === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', !light)
    try {
      localStorage.setItem(THEME_KEY, light ? '1' : '0')
    } catch {
      // ignore storage errors
    }
  }, [light])

  return { light, toggle: () => setLight((v) => !v) }
}

const TITLES: Record<string, string> = {
  '/': 'Dashboard',
  '/actions': 'Simple Actions',
  '/workflows': 'Workflows',
  '/convert': 'Convert',
  '/upload': 'Upload',
  '/templates': 'Templates',
  '/pack': 'Batch Pack',
  '/output': 'Output',
  '/jobs': 'Jobs',
  '/apps': 'Apps Hub',
  '/chat': 'Chat',
  '/live-write': 'Live Write',
  '/tools': 'Tools Hub',
  '/settings': 'Settings',
  '/skills': 'Skills',
  '/tests': 'Tests',
  '/logs': 'Logs',
  '/api-docs': 'API Docs',
  '/status': 'Status',
  '/help': 'Help',
}

function ToastItem({ t }: { t: Toast }) {
  const { removeToast } = useStore()
  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 40 }}
      className={[
        'flex items-start gap-3 px-4 py-3 rounded-lg border text-sm max-w-sm shadow-xl',
        t.type === 'success'
          ? 'bg-ink-800 border-acid/30 text-acid'
          : t.type === 'error'
            ? 'bg-ink-800 border-red-500/30 text-red-400'
            : 'bg-ink-800 border-amber-500/30 text-amber-300',
      ].join(' ')}
    >
      <span className="flex-1">{t.message}</span>
      <button
        type="button"
        onClick={() => removeToast(t.id)}
        className="opacity-50 hover:opacity-100"
      >
        <X size={12} />
      </button>
    </motion.div>
  )
}

export function Topbar() {
  const location = useLocation()
  const { toasts, setHelpOpen, health } = useStore()
  const title = TITLES[location.pathname] ?? location.pathname
  const be = health?.ports?.backend
  const fe = health?.ports?.frontend
  const { light, toggle } = useExperimentalTheme()

  return (
    <>
      <header className="h-14 flex items-center justify-between px-6 border-b border-ink-700 bg-ink-900/80 backdrop-blur-sm flex-shrink-0">
        <h1 className="font-display text-sm text-ink-400 tracking-wider uppercase">
          {title}
        </h1>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={toggle}
            className="text-ink-500 hover:text-amber-400 transition-colors"
            title={
              light
                ? 'Switch to dark (experimental light mode)'
                : 'Switch to light (experimental, ugly)'
            }
            aria-label="Toggle light mode (experimental)"
          >
            {light ? <Moon size={16} /> : <Sun size={16} />}
          </button>
          <span className="text-xs font-mono text-ink-600">
            {be && fe ? `:${be} / :${fe}` : '-'}
          </span>
          <button
            type="button"
            onClick={() => setHelpOpen(true)}
            className="text-ink-500 hover:text-amber-400 transition-colors"
            title="Help"
          >
            <HelpCircle size={16} />
          </button>
        </div>
      </header>

      <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
        <AnimatePresence>
          {toasts.map((t) => (
            <ToastItem key={t.id} t={t} />
          ))}
        </AnimatePresence>
      </div>
    </>
  )
}
