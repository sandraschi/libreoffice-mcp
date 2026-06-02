import { motion } from 'framer-motion'
import { Circle, ExternalLink, Grid3X3, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { api, type FleetAppEntry } from '../lib/api'

async function probePort(port: number): Promise<boolean> {
  try {
    const r = await fetch(`http://127.0.0.1:${port}/api/health`, {
      signal: AbortSignal.timeout(1500),
    })
    if (r.ok) return true
  } catch {
    /* try /health */
  }
  try {
    const r = await fetch(`http://127.0.0.1:${port}/health`, {
      signal: AbortSignal.timeout(1500),
    })
    return r.ok
  } catch {
    return false
  }
}

export function Apps() {
  const [apps, setApps] = useState<Array<FleetAppEntry & { alive: boolean }>>(
    [],
  )
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      try {
        const manifest = await api.fleetApps()
        const probed = await Promise.all(
          manifest.map(async (entry) => ({
            ...entry,
            alive: entry.port ? await probePort(entry.port) : false,
          })),
        )
        if (!cancelled) setApps(probed)
      } catch {
        if (!cancelled) setApps([])
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    const timer = window.setInterval(load, 60_000)
    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  const alive = apps.filter((a) => a.alive)
  const dead = apps.filter((a) => !a.alive)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6 max-w-5xl"
    >
      <div>
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <Grid3X3 size={20} className="text-amber-400" />
          Fleet Apps Hub
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          Live discovery from mcp-central-docs webapp-registry — probes
          localhost health endpoints
        </p>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-ink-500 text-sm">
          <Loader2 size={16} className="animate-spin" />
          Discovering fleet webapps…
        </div>
      ) : (
        <>
          {alive.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-medium text-ink-400">
                Online ({alive.length})
              </h2>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                {alive.map((app, i) => (
                  <motion.a
                    key={app.id}
                    href={app.url || `http://127.0.0.1:${app.port}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.03 }}
                    className="rounded-lg border border-ink-700 bg-ink-900 p-4 hover:border-amber-500/40 transition-colors group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Circle size={8} className="fill-acid text-acid" />
                        <span className="text-sm font-medium text-ink-100">
                          {app.name}
                        </span>
                      </div>
                      <ExternalLink
                        size={14}
                        className="text-ink-600 group-hover:text-amber-400"
                      />
                    </div>
                    <div className="text-xs font-mono text-ink-500">
                      :{app.port}
                    </div>
                    {app.repo && (
                      <div className="text-xs text-ink-600 mt-1 truncate">
                        {app.repo}
                      </div>
                    )}
                  </motion.a>
                ))}
              </div>
            </section>
          )}

          {dead.length > 0 && (
            <section className="space-y-3">
              <h2 className="text-sm font-medium text-ink-600">
                Offline ({dead.length})
              </h2>
              <div className="grid grid-cols-3 lg:grid-cols-4 gap-2">
                {dead.map((app) => (
                  <div
                    key={app.id}
                    className="rounded-md border border-ink-800 bg-ink-900/50 px-3 py-2 opacity-50"
                  >
                    <div className="text-xs text-ink-500 truncate">
                      {app.name}
                    </div>
                    <div className="text-xs font-mono text-ink-600">
                      :{app.port}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {apps.length === 0 && (
            <p className="text-sm text-ink-500">
              No apps in registry — check LIBREOFFICE_MCP_CENTRAL_DOCS_PATH
            </p>
          )}
        </>
      )}
    </motion.div>
  )
}
