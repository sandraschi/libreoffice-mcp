import { AnimatePresence, motion } from 'framer-motion'
import {
  Activity,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  FileInput,
  FileStack,
  FileText,
  FlaskConical,
  FolderOpen,
  GitBranch,
  Grid3X3,
  HelpCircle,
  Layers,
  LayoutDashboard,
  MessageSquare,
  PenLine,
  ScrollText,
  Settings,
  Upload,
  Wrench,
  Zap,
} from 'lucide-react'
import { useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { api } from '../../lib/api'
import { useStore } from '../../store'

const NAV = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/actions', icon: Zap, label: 'Simple Actions' },
  { to: '/workflows', icon: GitBranch, label: 'Workflows' },
  { to: '/convert', icon: FileInput, label: 'Convert' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/templates', icon: FileText, label: 'Templates' },
  { to: '/pack', icon: FileStack, label: 'Batch Pack' },
  { to: '/output', icon: FolderOpen, label: 'Output' },
  { to: '/jobs', icon: Layers, label: 'Jobs' },
  { to: '/apps', icon: Grid3X3, label: 'Apps Hub' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/live-write', icon: PenLine, label: 'Live Write' },
  { to: '/tools', icon: Wrench, label: 'Tools' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/skills', icon: BookOpen, label: 'Skills' },
  { to: '/tests', icon: FlaskConical, label: 'Tests' },
  { to: '/logs', icon: ScrollText, label: 'Logs' },
  { to: '/api-docs', icon: BookOpen, label: 'API Docs' },
  { to: '/status', icon: Activity, label: 'Status' },
  { to: '/help', icon: HelpCircle, label: 'Help' },
]

export function Sidebar() {
  const { sidebarOpen, toggleSidebar, health, setHealth } = useStore()
  const location = useLocation()

  useEffect(() => {
    const load = () =>
      api
        .health()
        .then(setHealth)
        .catch(() => {})
    load()
    const timer = window.setInterval(load, 15000)
    return () => window.clearInterval(timer)
  }, [setHealth])

  const loOk = health?.soffice_available
  const bridgeOk = health?.extension_bridge_online

  return (
    <motion.aside
      animate={{ width: sidebarOpen ? 220 : 56 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="h-screen flex flex-col border-r border-ink-700 bg-ink-900 relative flex-shrink-0 overflow-hidden"
    >
      <div className="flex items-center h-14 px-3 border-b border-ink-700 overflow-hidden">
        <span className="text-amber-400 font-display text-lg font-medium whitespace-nowrap">
          {sidebarOpen ? 'LibreOffice MCP' : 'LO'}
        </span>
        {sidebarOpen && (
          <span className="ml-2 text-xs text-ink-500 font-mono whitespace-nowrap">
            v0.3 α
          </span>
        )}
      </div>

      <nav className="flex-1 py-4 space-y-1 px-2 overflow-hidden">
        {NAV.map(({ to, icon: Icon, label }) => {
          const active =
            to === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(to)
          return (
            <NavLink
              key={to}
              to={to}
              className={[
                'flex items-center gap-3 px-2 py-2 rounded-md text-sm transition-colors whitespace-nowrap overflow-hidden',
                active
                  ? 'bg-amber-500/10 text-amber-400'
                  : 'text-ink-500 hover:text-ink-200 hover:bg-ink-800',
              ].join(' ')}
            >
              <Icon size={16} className="flex-shrink-0" />
              <AnimatePresence>
                {sidebarOpen && (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    {label}
                  </motion.span>
                )}
              </AnimatePresence>
            </NavLink>
          )
        })}
      </nav>

      <div className="px-3 py-3 border-t border-ink-700 space-y-2 overflow-hidden">
        <div className="flex items-center gap-2">
          <span
            className={[
              'w-2 h-2 rounded-full flex-shrink-0',
              loOk ? 'bg-acid' : 'bg-red-500',
            ].join(' ')}
          />
          {sidebarOpen && (
            <span className="text-xs text-ink-500 truncate">
              {loOk
                ? `LO ${health?.soffice_version ?? 'ready'}`
                : 'soffice missing'}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span
            className={[
              'w-2 h-2 rounded-full flex-shrink-0',
              bridgeOk ? 'bg-acid' : 'bg-ink-600',
            ].join(' ')}
          />
          {sidebarOpen && (
            <span className="text-xs text-ink-500 truncate">
              {bridgeOk
                ? `Bridge :8765 (${health?.extension_tool_count ?? 0})`
                : 'Extension offline'}
            </span>
          )}
        </div>
      </div>

      <button
        type="button"
        onClick={toggleSidebar}
        className="absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-ink-700 border border-ink-600 flex items-center justify-center text-ink-400 hover:text-amber-400 hover:border-amber-500 transition-colors z-10"
      >
        {sidebarOpen ? <ChevronLeft size={12} /> : <ChevronRight size={12} />}
      </button>
    </motion.aside>
  )
}
