'use client'
import { useEffect, useState } from 'react'
import { Brain, Wrench, Layers, GitBranch, Database } from 'lucide-react'
import { monad } from '@/lib/api'
import { Card, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'

export default function RightRail({ refreshKey }: { refreshKey: number }) {
  const [info, setInfo] = useState<any>(null)
  const [tools, setTools] = useState<any[]>([])
  const [organs, setOrgans] = useState<any>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancel = false
    Promise.allSettled([monad.info(), monad.tools(), monad.organs()])
      .then(([i, t, o]) => {
        if (cancel) return
        if (i.status === 'fulfilled') setInfo(i.value); else setFailed(true)
        if (t.status === 'fulfilled') setTools(t.value)
        if (o.status === 'fulfilled') setOrgans(o.value)
      })
    return () => { cancel = true }
  }, [refreshKey])

  return (
    <aside className="hidden lg:flex w-80 flex-col border-l border-border-soft glass
                      overflow-y-auto p-4 gap-4">
      {/* Status */}
      <Card>
        <CardTitle className="flex items-center gap-2">
          <Brain className="w-4 h-4 text-accent-purple" /> System
        </CardTitle>
        {failed ? (
          <div className="text-xs text-accent-red mt-2">Backend not reachable.<br />
            Run <code className="text-accent-purple">monad serve</code> in a terminal.</div>
        ) : info ? (
          <div className="mt-3 space-y-1.5 text-xs text-text-soft">
            <Row k="Version" v={info.version || '?'} />
            <Row k="Codename" v={info.codename || '?'} />
            <Row k="Ready" v={info.health?.ready ? '✔' : '…'} />
            {info.cognition?.organs && (
              <Row k="Organs" v={String(info.cognition.organs.total)} />
            )}
            {info.memory?.store && (
              <Row k="Memories" v={`${info.memory.store.events} events`} />
            )}
          </div>
        ) : (
          <SkeletonRows n={4} />
        )}
      </Card>

      {/* Organs */}
      <Card>
        <CardTitle className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-accent-pink" /> Cognitive Organs
        </CardTitle>
        {organs ? (
          <div className="mt-3">
            <div className="flex flex-wrap gap-1">
              <Badge tone="purple">{organs.counts.human_genius} human</Badge>
              <Badge tone="blue">{organs.counts.animal_extreme} animal</Badge>
              <Badge tone="green">{organs.counts.microbial} microbial</Badge>
              <Badge tone="amber">{organs.counts.conceptual} conceptual</Badge>
            </div>
            <div className="text-xs text-text-muted mt-2">
              {organs.counts.total} organs total. All contribute to every cognition-enabled thought cycle.
            </div>
          </div>
        ) : <SkeletonRows n={2} />}
      </Card>

      {/* Tools */}
      <Card>
        <CardTitle className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-accent-blue" /> Tools
        </CardTitle>
        <div className="mt-3 space-y-1.5">
          {tools.length > 0 ? tools.map(t => (
            <div key={t.id} className="flex items-center justify-between text-xs">
              <span className="text-text-soft">{t.name}</span>
              {t.requires_approval && <Badge tone="amber">approval</Badge>}
            </div>
          )) : <SkeletonRows n={4} />}
          <div className="mt-2 text-[11px] text-text-muted">
            Type <code className="text-accent-purple">run tool &lt;id&gt;</code> in chat.
          </div>
        </div>
      </Card>

      {/* Evolution */}
      <Card>
        <CardTitle className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-accent-green" /> Self-Improvement
        </CardTitle>
        <div className="mt-3 text-xs text-text-soft space-y-1.5">
          <div>Ask Monad to <em>evolve</em> a new capability:</div>
          <code className="block bg-bg-soft rounded p-2 text-[11px] text-accent-purple">
            evolve: add a Bluetooth scanner tool
          </code>
          <div className="text-text-muted text-[11px]">
            Proposals are tested in a sandbox and require your approval.
          </div>
        </div>
      </Card>
    </aside>
  )
}

function Row({ k, v }: { k: string; v: string | number }) {
  return (
    <div className="flex justify-between">
      <span className="text-text-muted">{k}</span>
      <span className="text-text-DEFAULT font-medium">{v}</span>
    </div>
  )
}

function SkeletonRows({ n }: { n: number }) {
  return (
    <div className="mt-3 space-y-2">
      {Array.from({ length: n }).map((_, i) => (
        <div key={i} className="h-3 bg-bg-hover rounded animate-pulse" style={{ width: `${60 + (i * 7) % 30}%` }} />
      ))}
    </div>
  )
}
