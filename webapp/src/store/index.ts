import { create } from 'zustand'
import type { Health, Job, ProviderInfo } from '../lib/api'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

interface AppState {
  health: Health | null
  setHealth: (h: Health) => void
  sidebarOpen: boolean
  toggleSidebar: () => void
  jobs: Job[]
  setJobs: (jobs: Job[]) => void
  helpOpen: boolean
  setHelpOpen: (open: boolean) => void
  toasts: Toast[]
  addToast: (t: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  providers: ProviderInfo[]
  setProviders: (p: ProviderInfo[]) => void
  gpuDetected: boolean
  setGpuDetected: (d: boolean) => void
}

let _tid = 0

export const useStore = create<AppState>((set) => ({
  health: null,
  setHealth: (health) => set({ health }),
  sidebarOpen: true,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  jobs: [],
  setJobs: (jobs) => set({ jobs }),
  helpOpen: false,
  setHelpOpen: (helpOpen) => set({ helpOpen }),
  toasts: [],
  addToast: (t) => {
    const id = String(++_tid)
    set((s) => ({ toasts: [...s.toasts, { ...t, id }] }))
    setTimeout(
      () => set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })),
      4500,
    )
  },
  removeToast: (id) =>
    set((s) => ({ toasts: s.toasts.filter((x) => x.id !== id) })),
  providers: [],
  setProviders: (providers) => set({ providers }),
  gpuDetected: false,
  setGpuDetected: (gpuDetected) => set({ gpuDetected }),
}))
