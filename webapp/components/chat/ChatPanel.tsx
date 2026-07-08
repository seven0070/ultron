'use client'
import { useEffect, useRef, useState } from 'react'
import { Send, Sparkles, Brain, GitBranch, BookOpen, Wrench, Database, Loader2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { monad } from '@/lib/api'
import { parseCommand, type Command } from '@/lib/commands'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import MessageBubble, { type Message } from './MessageBubble'
import QuickActions from './QuickActions'

export default function ChatPanel({
  sessionId, onAction,
}: { sessionId: string; onAction?: () => void }) {
  const [messages, setMessages] = useState<Message[]>(() => [{
    id: 'welcome', role: 'assistant',
    content: `Welcome to Monad. I'm a portable cognitive AI with 82 organs, self-improvement, and multi-model fusion.

**Try these:**
- *Just ask anything* — I'll route to the right model
- *"fuse: <question>"* — 3 models produce one unified answer
- *"learn this: <paste any text>"* — I'll remember it
- *"integrate https://github.com/…"* — analyze & propose integration
- *"evolve: add a plugin that <goal>"* — I'll draft, test, and ask approval
- *"remember: <fact>"* / *"recall <query>"* — persistent memory
- *"/help"* — see all commands

What are we working on?`,
    ts: new Date().toISOString(),
  }])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)
  const [useCognition, setUseCognition] = useState(true)
  const [useFusion, setUseFusion] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  async function send(overrideInput?: string) {
    const text = (overrideInput ?? input).trim()
    if (!text || busy) return
    setInput('')
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user',
                                content: text, ts: new Date().toISOString() }
    setMessages(m => [...m, userMsg])
    setBusy(true)

    const cmd = parseCommand(text)
    try {
      const reply = await dispatch(cmd, { useCognition, useFusion })
      setMessages(m => [...m, {
        id: crypto.randomUUID(), role: 'assistant',
        content: reply.content, meta: reply.meta,
        ts: new Date().toISOString(),
      }])
      onAction?.()
    } catch (e: any) {
      setMessages(m => [...m, {
        id: crypto.randomUUID(), role: 'assistant',
        content: `⚠️ **Error:** ${e.message || String(e)}\n\nIf this says *"failed to fetch"*, the Monad backend may not be running. Start it with:\n\n\`\`\`bash\nmonad serve\n\`\`\``,
        ts: new Date().toISOString(), meta: { error: true },
      }])
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Header */}
      <div className="h-14 border-b border-border-soft glass flex items-center px-4 gap-3">
        <div className="w-8 h-8 rounded-lg bg-monad-gradient flex items-center justify-center">
          <Brain className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">Monad</div>
          <div className="text-xs text-text-muted">session {sessionId.slice(0, 8)}</div>
        </div>
        <ModeToggle
          label="Cognition" active={useCognition} onToggle={() => setUseCognition(x => !x)}
          tone="purple" icon={<Brain className="w-3 h-3" />}
        />
        <ModeToggle
          label="Fusion" active={useFusion} onToggle={() => setUseFusion(x => !x)}
          tone="pink" icon={<Sparkles className="w-3 h-3" />}
        />
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          <AnimatePresence initial={false}>
            {messages.map(m => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
              >
                <MessageBubble message={m} />
              </motion.div>
            ))}
          </AnimatePresence>
          {busy && <TypingIndicator />}
        </div>
      </div>

      {/* Quick actions */}
      {messages.length <= 2 && (
        <QuickActions onPick={q => { setInput(q); setTimeout(() => send(q), 50) }} />
      )}

      {/* Composer */}
      <div className="border-t border-border-soft glass p-3 md:p-4">
        <div className="max-w-3xl mx-auto flex items-end gap-2">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
            }}
            placeholder="Ask, learn, integrate, evolve…  (shift+enter for newline)"
            className="flex-1 bg-bg-soft border border-border rounded-xl px-4 py-3
                       text-sm resize-none focus:outline-none focus:border-accent-purple
                       placeholder:text-text-muted min-h-[52px] max-h-40"
            rows={1}
            disabled={busy}
          />
          <Button onClick={() => send()} disabled={busy || !input.trim()}
                  className="h-[52px] w-[52px] justify-center p-0">
            {busy ? <Loader2 className="w-5 h-5 animate-spin" />
                  : <Send className="w-5 h-5" />}
          </Button>
        </div>
        <div className="max-w-3xl mx-auto mt-2 flex items-center gap-2 text-[11px] text-text-muted">
          <span>Enter to send · Shift+Enter for newline · Try <code className="text-accent-purple">integrate</code>, <code className="text-accent-purple">learn</code>, <code className="text-accent-purple">evolve</code>, <code className="text-accent-purple">fuse</code></span>
        </div>
      </div>
    </div>
  )
}

function ModeToggle({ label, active, onToggle, tone, icon }:
  { label: string; active: boolean; onToggle: () => void;
    tone: 'purple'|'pink'; icon: React.ReactNode }) {
  return (
    <button
      onClick={onToggle}
      className={`px-2.5 py-1 rounded-md text-xs font-medium border transition
        flex items-center gap-1.5
        ${active
          ? tone === 'purple'
            ? 'bg-accent-purple/20 text-accent-purple border-accent-purple/40'
            : 'bg-accent-pink/20 text-accent-pink border-accent-pink/40'
          : 'text-text-muted border-border hover:text-text-DEFAULT'}`}
    >
      {icon}{label}
    </button>
  )
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-2 text-text-muted text-sm py-2">
      <div className="w-2 h-2 rounded-full bg-accent-purple animate-pulse" />
      <div className="w-2 h-2 rounded-full bg-accent-pink animate-pulse" style={{ animationDelay: '0.15s' }} />
      <div className="w-2 h-2 rounded-full bg-accent-blue animate-pulse" style={{ animationDelay: '0.3s' }} />
      <span className="ml-2">Monad is thinking…</span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Command dispatcher — parses the intent and calls the right endpoint(s)
// ---------------------------------------------------------------------------

async function dispatch(cmd: Command, opts: { useCognition: boolean; useFusion: boolean }) {
  switch (cmd.kind) {
    case 'help':
      return { content: HELP_TEXT, meta: { kind: 'help' } }

    case 'ask': {
      if (opts.useFusion) {
        const r = await monad.fuse(cmd.prompt, 'auto')
        return { content: r.text || '_(no output)_',
                 meta: { kind: 'fuse', ...r } }
      }
      const r = await monad.ask(cmd.prompt, {
        cognition: cmd.cognition ?? opts.useCognition,
      })
      return { content: r.text || '_(no output)_',
               meta: { kind: 'ask', model: r.model, latency: r.latency_ms,
                       trace: r.trace } }
    }

    case 'fuse': {
      const r = await monad.fuse(cmd.prompt, cmd.mode)
      return { content: r.text || '_(no output)_',
               meta: { kind: 'fuse', mode: r.mode_used, latency: r.latency_ms,
                       fallback: r.fallback_reason, trace: r.trace } }
    }

    case 'learn': {
      const r = await monad.learn(cmd.source, cmd.sourceKind)
      return {
        content: `📚 **Learned.** ${r.summary || `Ingested ${cmd.sourceKind}: ${cmd.source.slice(0, 80)}${cmd.source.length > 80 ? '…' : ''}`}\n\n${r.chunks ? `${r.chunks} chunk(s) added to memory.` : ''}`,
        meta: { kind: 'learn', ...r },
      }
    }

    case 'integrate': {
      const r = await monad.learn(cmd.url, 'repo')
      return {
        content: `🔗 **Integration analysis of** \`${cmd.url}\`\n\n${r.summary || 'Fetched and analyzed.'}\n\n${r.next_steps ? `**Next steps:**\n${r.next_steps}` : ''}\n\n> Say *"evolve: integrate this into <path>"* to actually wire it in.`,
        meta: { kind: 'integrate', ...r },
      }
    }

    case 'evolve': {
      const target = cmd.target || `monad/plugins/auto_${Date.now()}.py`
      const r = await monad.evolvePropose(cmd.goal, target, cmd.zone || 'plugins')
      return {
        content: `🧬 **Proposal drafted** (id: \`${r.record_id || r.id}\`)\n\n**Goal:** ${cmd.goal}\n**Target:** \`${target}\`\n**Model:** ${r.model_used || 'stub'}\n\n${r.rationale ? `**Rationale:** ${r.rationale}\n\n` : ''}${r.diff_preview ? `\`\`\`diff\n${r.diff_preview.slice(0, 1200)}\n\`\`\`\n\n` : ''}Approve in the sidebar → Evolution to apply, or say *"cancel"*.`,
        meta: { kind: 'evolve', ...r },
      }
    }

    case 'remember': {
      const r = await monad.remember(cmd.text)
      return { content: `💾 Remembered as event-${r.event_id}.`,
               meta: { kind: 'remember', ...r } }
    }

    case 'recall': {
      const r = await monad.recall(cmd.query)
      const lines = (r.results || []).map((h: any, i: number) =>
        `${i + 1}. \`[${(h.score ?? 0).toFixed(2)}]\` ${h.text?.slice(0, 200) || ''}`).join('\n')
      return {
        content: r.results?.length
          ? `🔍 **${r.results.length} match(es) for** *"${cmd.query}"*:\n\n${lines}`
          : `🤷 No memory found for *"${cmd.query}"*.`,
        meta: { kind: 'recall', hits: r.results },
      }
    }

    case 'forget': {
      // No dedicated /forget endpoint yet — approximate via memory query
      return { content: `⚠️ Forget endpoint not yet wired in the web backend. Use CLI: \`monad memory forget "${cmd.needle}"\``,
               meta: { kind: 'forget' } }
    }

    case 'tool': {
      const r = await monad.runTool(cmd.id, cmd.kwargs)
      return {
        content: `🛠 **Tool** \`${cmd.id}\` — ${r.ok ? '✔ ok' : '✘ failed'}\n\n\`\`\`json\n${JSON.stringify(r.output ?? r.error, null, 2).slice(0, 1500)}\n\`\`\``,
        meta: { kind: 'tool', ...r },
      }
    }
  }
}

const HELP_TEXT = `**Monad commands** (all also work with a leading \`/\`):

- \`<anything>\` — normal question (routed to the right model)
- \`fuse: <question>\` — all models fuse into one answer
- \`fuse chain|ensemble|logits: <question>\` — force a fusion mode
- \`learn: <text or paste>\` — persist to memory
- \`learn: <url>\` — fetch + ingest
- \`integrate <github url>\` — analyze a repo for integration
- \`evolve: <goal>\` — draft a code change (approval-gated)
- \`evolve: <goal> into <path>\` — target a specific file
- \`remember: <fact>\` — pin something
- \`recall <query>\` — search memory
- \`run tool <id> [args]\` — invoke a Monad tool
- \`/cog <question>\` — force cognition pre-pass

Toggle **Cognition** (adds 82-organ pre-pass) or **Fusion** (multi-model merge) in the header.`
