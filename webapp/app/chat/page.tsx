'use client'
import { useState } from 'react'
import Sidebar from '@/components/layout/Sidebar'
import ChatPanel from '@/components/chat/ChatPanel'
import RightRail from '@/components/layout/RightRail'

export default function ChatPage() {
  const [sessionId, setSessionId] = useState<string>(() =>
    typeof window !== 'undefined'
      ? (localStorage.getItem('monad-session') || crypto.randomUUID())
      : 'default'
  )
  const [refreshKey, setRefreshKey] = useState(0)
  const bump = () => setRefreshKey(k => k + 1)

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar sessionId={sessionId} onNewSession={() => {
        const id = crypto.randomUUID()
        localStorage.setItem('monad-session', id)
        setSessionId(id); bump()
      }} refreshKey={refreshKey} />

      <main className="flex-1 flex flex-col min-w-0">
        <ChatPanel sessionId={sessionId} onAction={bump} />
      </main>

      <RightRail refreshKey={refreshKey} />
    </div>
  )
}
