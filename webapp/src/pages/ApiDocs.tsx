import { motion } from 'framer-motion'
import { BookOpen } from 'lucide-react'

export function ApiDocs() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-[calc(100vh-8rem)]"
    >
      <div className="mb-4">
        <h1 className="text-xl font-display text-ink-100 flex items-center gap-2">
          <BookOpen size={20} className="text-amber-400" />
          API Docs
        </h1>
        <p className="text-sm text-ink-500 mt-1">
          FastAPI Swagger UI — proxied from backend :10981
        </p>
      </div>
      <iframe
        title="OpenAPI Swagger"
        src="/docs"
        className="flex-1 w-full rounded-lg border border-ink-700 bg-white min-h-0"
      />
    </motion.div>
  )
}
