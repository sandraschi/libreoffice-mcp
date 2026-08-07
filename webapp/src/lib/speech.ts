const SPEECH_BASE =
  import.meta.env.VITE_SPEECH_MCP_URL ?? 'http://127.0.0.1:10909'

export async function speakText(text: string): Promise<void> {
  const trimmed = text.trim().slice(0, 8000)
  if (!trimmed) return

  const q = new URLSearchParams({ text: trimmed, provider: 'windows' })
  const res = await fetch(`${SPEECH_BASE}/api/v1/tts/wav?${q}`)
  if (!res.ok) {
    throw new Error(`TTS failed (${res.status})`)
  }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  try {
    await new Audio(url).play()
  } finally {
    URL.revokeObjectURL(url)
  }
}
