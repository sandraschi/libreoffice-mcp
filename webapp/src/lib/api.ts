export type Health = {
  status: string
  version: string
  soffice_available: boolean
  soffice_path: string | null
  soffice_version: string | null
  extension_bridge_online: boolean
  extension_bridge_url?: string
  extension_tool_count: number
  writer_bridge_connected?: boolean
  output_dir: string
  templates_dir: string
  ports: { backend: number; frontend: number }
}

export type Job = {
  id: string
  name: string
  status: 'running' | 'done' | 'error'
  input: string
  output_format: string
  started: string
  finished: string | null
  result: { output?: string } | null
  error: string | null
}

export type OutputFile = {
  name: string
  path: string
  size_bytes: number
  modified?: number
  previewable?: boolean
}

export type TemplateInfo = {
  name: string
  path: string
  description: string
  placeholders: string[]
}

export type PortmanteauOp = {
  name: string
  description: string
}

export type ToolInfo = {
  name: string
  kind: string
  description: string
  operations: PortmanteauOp[]
}

export type HelpInfo = {
  title: string
  version: string
  ports: Record<string, number>
  host: { soffice: string; env: string[] }
  coworker_flows: string[]
  templates: string[]
}

export type SimpleActionDef = {
  id: string
  label: string
  description: string
  operation: string
  params: Array<Record<string, unknown>>
  dynamic_placeholders?: boolean
}

export type WorkflowPlaceholder = {
  key: string
  label: string
  default?: string
  default_from?: string
  multiline?: boolean
}

export type WorkflowDef = {
  id: string
  label: string
  description: string
  template?: string
  coworker_flow?: string
  output_stem_default?: string
  operation?: string
  placeholders?: WorkflowPlaceholder[]
  params?: Array<Record<string, unknown>>
}

export type ActionCatalog = {
  simple_actions: SimpleActionDef[]
  workflows: WorkflowDef[]
  templates: TemplateInfo[]
  defaults: { today: string }
}

export type AgenticPlan = {
  success: boolean
  goal?: string
  steps?: Array<Record<string, unknown>>
  message?: string
  executed?: boolean
  results?: Array<Record<string, unknown>>
  error?: string
  llm_hint?: Record<string, unknown>
}

export type SkillEntry = {
  id: string
  name: string
  description: string
  uri: string
  path?: string
  content?: string
}

export type Capabilities = {
  features: Record<string, boolean>
  integrations: Record<string, string | null>
}

export type SelfTestRow = { name: string; ok: boolean; detail?: string }
export type SelfTestResult = {
  success: boolean
  passed: number
  total: number
  results: SelfTestRow[]
}

export type UploadResult = {
  success: boolean
  path: string
  name: string
  size_bytes: number
  document: Record<string, unknown>
}

export type FleetAppEntry = {
  id: string
  name: string
  port: number
  url: string
  repo?: string | null
  repo_path?: string | null
}

export type LogEntry = {
  timestamp: string
  level: string
  name: string
  message: string
}

/** Empty in dev (Vite proxy); direct backend URL in Tauri production build. */
export const API_BASE = import.meta.env.DEV ? '' : 'http://127.0.0.1:10981'

export function apiPath(path: string): string {
  return `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
}

/** Patch fetch/EventSource for Tauri production (relative /api paths). */
export function installTauriApiShim(): void {
  if (import.meta.env.DEV) return

  const base = API_BASE
  const origFetch = window.fetch.bind(window)
  window.fetch = (input: RequestInfo | URL, init?: RequestInit) => {
    if (typeof input === 'string' && input.startsWith('/')) {
      return origFetch(base + input, init)
    }
    return origFetch(input, init)
  }

  const OrigES = window.EventSource
  window.EventSource = class PatchedEventSource extends OrigES {
    constructor(url: string | URL, config?: EventSourceInit) {
      const resolved =
        typeof url === 'string' && url.startsWith('/') ? base + url : url
      super(resolved, config)
    }
  } as typeof EventSource
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(apiPath(path))
  if (!res.ok) {
    throw new Error(`${path} → ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(apiPath(path), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = (await res.json()) as T & { detail?: string }
  if (!res.ok) {
    throw new Error(data.detail ?? `${path} → ${res.status}`)
  }
  return data
}

export const api = {
  health: () => getJson<Health>('/health'),
  capabilities: () => getJson<Capabilities>('/api/capabilities'),
  logs: () => getJson<{ logs: LogEntry[] }>('/api/logs'),
  fleetApps: () =>
    getJson<{ apps: FleetAppEntry[] }>('/api/fleet/apps').then((r) => r.apps),
  env: () => getJson<Record<string, string | null>>('/api/env'),
  saveEnv: (values: Record<string, string>) =>
    postJson<{ ok: boolean; message: string }>('/api/env', values),
  testLlm: (body: {
    provider: string
    base_url?: string
    model?: string
    api_key?: string
  }) => postJson<{ ok: boolean; message?: string }>('/api/test-llm', body),
  status: () =>
    getJson<{ success: boolean; data: Record<string, unknown> }>('/api/status'),
  jobs: () => getJson<{ jobs: Job[] }>('/api/jobs'),
  output: () =>
    getJson<{ files: OutputFile[]; output_dir: string }>('/api/output'),
  templates: () => getJson<{ templates: TemplateInfo[] }>('/api/templates'),
  tools: () => getJson<{ tools: ToolInfo[] }>('/api/tools'),
  help: () => getJson<HelpInfo>('/api/help'),
  previewUrl: (filename: string) =>
    apiPath(`/api/output/file/${encodeURIComponent(filename)}`),
  convert: (input_path: string, output_format: string) =>
    postJson<{ job: Job; message: string }>('/api/convert', {
      input_path,
      output_format,
    }),
  merge: (
    template: string,
    placeholders: Record<string, string>,
    output_format: string,
    output_stem?: string,
  ) =>
    postJson<{ data: { output?: string }; message: string }>('/api/merge', {
      template,
      placeholders,
      output_format,
      output_stem,
    }),
  pack: (
    input_paths: string[],
    title: string,
    output_format: string,
    output_stem?: string,
  ) =>
    postJson<{ data: { output?: string; count?: number }; message: string }>(
      '/api/pack',
      {
        input_paths,
        title,
        output_format,
        output_stem,
      },
    ),
  actionsCatalog: () =>
    getJson<ActionCatalog & { success?: boolean }>('/api/actions').then(
      ({ simple_actions, workflows, templates, defaults }) => ({
        simple_actions,
        workflows,
        templates,
        defaults,
      }),
    ),
  runAction: (action_id: string, params: Record<string, unknown>) =>
    postJson<{ success: boolean; message?: string; data?: unknown }>(
      '/api/actions/run',
      { action_id, params },
    ),
  workflowsCatalog: () =>
    getJson<{
      workflows: WorkflowDef[]
      defaults: { today: string }
      templates: TemplateInfo[]
    }>('/api/workflows'),
  runWorkflow: (workflow_id: string, params: Record<string, unknown>) =>
    postJson<{ success: boolean; message?: string; data?: unknown }>(
      '/api/workflows/run',
      { workflow_id, params },
    ),
  agentic: (
    goal: string,
    opts?: {
      execute?: boolean
      params?: Record<string, unknown>
      use_llm?: boolean
    },
  ) =>
    postJson<AgenticPlan>('/api/agentic', {
      goal,
      execute: opts?.execute ?? false,
      params: opts?.params ?? {},
      use_llm: opts?.use_llm ?? false,
    }),
  skills: () =>
    getJson<{ skills: SkillEntry[] }>('/api/skills').then((r) => r.skills),
  skill: (id: string) =>
    getJson<{ skill: SkillEntry }>(
      `/api/skills/${encodeURIComponent(id)}`,
    ).then((r) => r.skill),
  chat: (message: string, execute = true) =>
    postJson<{ role: string; content: string; plan: AgenticPlan }>(
      '/api/chat',
      {
        message,
        execute,
      },
    ),
  upload: async (file: File): Promise<UploadResult> => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(apiPath('/api/upload'), {
      method: 'POST',
      body: form,
    })
    const data = (await res.json()) as UploadResult & { detail?: string }
    if (!res.ok) throw new Error(data.detail ?? `upload → ${res.status}`)
    return data
  },
  revealOutput: (filename: string) =>
    postJson<{ success: boolean; message?: string }>(
      `/api/output/reveal/${encodeURIComponent(filename)}`,
      {},
    ),
  runTests: (includeSoffice = true) =>
    getJson<SelfTestResult>(
      `/api/tests/run?include_soffice=${includeSoffice ? 'true' : 'false'}`,
    ),
  formats: (path?: string) =>
    path
      ? getJson<{ suggested_formats: string[] }>(
          `/api/formats?path=${encodeURIComponent(path)}`,
        )
      : getJson<{ writer: string[]; calc: string[]; impress: string[] }>(
          '/api/formats',
        ),
  liveStatus: () =>
    getJson<{
      writer_bridge_connected: boolean
      calc_bridge_connected?: boolean
      connected: boolean
      pending_tasks: number
    }>('/api/live/status'),
  calcLiveStatus: () =>
    getJson<{
      calc_bridge_connected: boolean
      connected: boolean
      pending_tasks: number
    }>('/api/live/calc/status'),
  liveWrite: (body: {
    prompt: string
    wpm?: number
    max_words?: number
    launch_writer?: boolean
  }) =>
    postJson<{ success: boolean; data: Record<string, unknown> }>(
      '/api/live/write',
      body,
    ),
  launchWriter: () =>
    postJson<{ success: boolean; message?: string }>(
      '/api/live/launch-writer',
      {},
    ),
  launchCalc: () =>
    postJson<{ success: boolean; message?: string }>(
      '/api/live/launch-calc',
      {},
    ),
  livePivotDemo: (body: {
    typewriter_seed?: boolean
    launch_calc?: boolean
  }) =>
    postJson<{ success: boolean; data: Record<string, unknown> }>(
      '/api/live/calc/pivot-demo',
      body,
    ),
}
