import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { HelpModal } from './components/HelpModal'
import { Sidebar } from './components/layout/Sidebar'
import { Topbar } from './components/layout/Topbar'
import { ApiDocs } from './pages/ApiDocs'
import { Apps } from './pages/Apps'
import { Chat } from './pages/Chat'
import { Convert } from './pages/Convert'
import { Dashboard } from './pages/Dashboard'
import { Help } from './pages/Help'
import { Jobs } from './pages/Jobs'
import { LiveCalcPage } from './pages/LiveCalc'
import { LiveWritePage } from './pages/LiveWrite'
import { Logs } from './pages/Logs'
import { Output } from './pages/Output'
import { Pack } from './pages/Pack'
import { SettingsPage } from './pages/SettingsPage'
import { SimpleActions } from './pages/SimpleActions'
import { Skills } from './pages/Skills'
import { Status } from './pages/Status'
import { Templates } from './pages/Templates'
import { TestsPage } from './pages/Tests'
import { Tools } from './pages/Tools'
import { UploadPage } from './pages/Upload'
import { Workflows } from './pages/Workflows'

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen overflow-hidden bg-ink-950">
        <Sidebar />
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <Topbar />
          <main className="flex-1 overflow-y-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/convert" element={<Convert />} />
              <Route path="/actions" element={<SimpleActions />} />
              <Route path="/workflows" element={<Workflows />} />
              <Route path="/templates" element={<Templates />} />
              <Route path="/pack" element={<Pack />} />
              <Route path="/output" element={<Output />} />
              <Route path="/jobs" element={<Jobs />} />
              <Route path="/apps" element={<Apps />} />
              <Route path="/chat" element={<Chat />} />
              <Route path="/live-write" element={<LiveWritePage />} />
              <Route path="/live-calc" element={<LiveCalcPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/tests" element={<TestsPage />} />
              <Route path="/tools" element={<Tools />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/skills" element={<Skills />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/api-docs" element={<ApiDocs />} />
              <Route path="/status" element={<Status />} />
              <Route path="/help" element={<Help />} />
            </Routes>
          </main>
        </div>
      </div>
      <HelpModal />
    </BrowserRouter>
  )
}
