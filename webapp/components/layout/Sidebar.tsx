'use client'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { Plus, MessageSquare, Settings, ExternalLink, Home } from 'lucide-react'
import { monad } from '@/lib/api'
import { Button } from '@/components/ui/Button'

export default function Sidebar({
  sessionId, onNewSession, refreshKey,
}: { sessionId: string; onNewSession: () => void; refreshKey: number }) {
  const [health, setHealth] = useState<{ ready?: boolean; version?: string } | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false
    monad.info()
      .then(i => { if (!cancelled) { setHealth(i); setFailed(false) } })
      .catch(() => { if (!cancelled) setFailed(true) })
    return () => { cancelled = true }
  }, [refreshKey])

  return (
    <aside className="hidden md:flex w-64 flex-col border-r border-border-soft glass">
      <div className="p-4 flex items-center gap-2">
        <Link href="/" className="flex items-center gap-2 flex-1">
          <span className="text-xl">🧠</span>
          <span className="font-semibold gradient-text">Monad</span>
        </Link>
        <Link href="/" title="Home" className="text-text-muted hover:text-text-DEFAULT">
          <Home className="w-4 h-4" />
        </Link>
      </div>

      <div className="px-3">
        <Button onClick={onNewSession} className="w-full justify-center">
          <Plus className="w-4 h-4" /> New chat
        </Button>
      </div>

      <div className="mt-6 px-4 text-xs uppercase tracking-wider text-text-muted">
        Session
      </div>
      <div className="px-2 mt-2">
        <div className="px-2 py-2 rounded-lg bg-bg-hover text-sm flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-accent-purple" />
          <span className="truncate text-text-soft">{sessionId.slice(0, 12)}…</span>
        </div>
      </div>

      <div className="mt-6 px-4 text-xs uppercase tracking-wider text-text-muted">
        Suggested prompts
      </div>
      <div className="px-2 mt-2 space-y-1 text-xs text-text-soft">
        {[
          'fuse: compare Python and Rust for a portable AI OS',
          'evolve: add a weather plugin',
          'integrate https://github.com/…',
          'learn: my project uses SQLite for memory',
        ].map(s => (
          <div key={s} className="px-2 py-2 rounded-lg hover:bg-bg-hover truncate cursor-pointer"
               title={s}>{s}</div>
        ))}
      </div>

      <div className="flex-1" />

      <div className="p-3 border-t border-border-soft">
        <div className="text-xs text-text-muted mb-2 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            failed ? 'bg-accent-red' : health?.ready ? 'bg-accent-green' : 'bg-accent-amber'
          } animate-pulse`} />
          {failed ? 'backend offline'
                  : health?.ready ? `Monad ${health.version || 'ready'}`
                                  : 'connecting…'}
        </div>
        <a href="/api/monad/docs" target="_blank" rel="noreferrer"
           className="text-xs text-text-muted hover:text-accent-purple flex items-center gap-1">
          API docs <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </aside>
  )
}
