export type LoFamily = 'writer' | 'calc' | 'impress'

const LS_KEY = 'libreoffice-mcp-last-lo-family'

export function familyForFile(name: string): LoFamily {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['ods', 'xlsx', 'csv', 'tsv'].includes(ext)) return 'calc'
  if (['odp', 'pptx', 'ppt'].includes(ext)) return 'impress'
  return 'writer'
}

export function rememberLoFamily(family: LoFamily): void {
  try {
    localStorage.setItem(LS_KEY, family)
  } catch {
    /* ignore */
  }
}

export function lastLoFamily(): LoFamily {
  try {
    const v = localStorage.getItem(LS_KEY)
    if (v === 'calc' || v === 'impress' || v === 'writer') return v
  } catch {
    /* ignore */
  }
  return 'writer'
}
