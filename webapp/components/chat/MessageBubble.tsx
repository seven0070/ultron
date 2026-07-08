'use client'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { User, Brain, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import { Badge } from '@/components/ui/Badge'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  ts: string
  meta?: Record<string, any>
}

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center
                       ${isUser ? 'bg-accent-blue/20' : 'bg-monad-gradient'}`}>
        {isUser ? <User className="w-4 h-4 text-accent-blue" />
                : <Brain className="w-4 h-4 text-white" />}
      </div>

      <div className={`flex-1 min-w-0 ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div className={`inline-block max-w-full rounded-2xl px-4 py-3
                         ${isUser
                           ? 'bg-accent-blue/10 border border-accent-blue/20'
                           : 'glass'}`}>
          <MarkdownBody content={message.content} />
        </div>

        {message.meta && !isUser && (
          <MetaChips meta={message.meta} />
        )}
      </div>
    </div>
  )
}

function MarkdownBody({ content }: { content: string }) {
  return (
    <div className="prose prose-invert prose-sm max-w-none
                    prose-p:my-2 prose-p:leading-relaxed
                    prose-headings:mt-3 prose-headings:mb-2
                    prose-code:before:content-none prose-code:after:content-none
                    prose-code:bg-bg-hover prose-code:px-1.5 prose-code:py-0.5
                    prose-code:rounded prose-code:text-accent-purple
                    prose-pre:bg-transparent prose-pre:p-0
                    prose-a:text-accent-blue hover:prose-a:text-accent-purple
                    prose-strong:text-text-DEFAULT
                    prose-ul:my-2 prose-ol:my-2 prose-li:my-0
                    prose-blockquote:border-accent-purple prose-blockquote:text-text-soft">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '')
            if (!inline && match) {
              return (
                <SyntaxHighlighter
                  language={match[1]} style={atomDark} PreTag="div"
                  customStyle={{ borderRadius: 8, marginTop: 8, marginBottom: 8, fontSize: 12 }}
                  {...props}
                >
                  {String(children).replace(/\n$/, '')}
                </SyntaxHighlighter>
              )
            }
            return <code className={className} {...props}>{children}</code>
          },
        }}
      >{content}</ReactMarkdown>
    </div>
  )
}

function MetaChips({ meta }: { meta: Record<string, any> }) {
  const [open, setOpen] = useState(false)
  const chips: { label: string; tone: any }[] = []

  if (meta.kind) chips.push({ label: meta.kind, tone: 'purple' })
  if (meta.mode) chips.push({ label: `mode: ${meta.mode}`, tone: 'blue' })
  if (meta.model) chips.push({ label: meta.model, tone: 'blue' })
  if (meta.latency != null) chips.push({ label: `${Math.round(meta.latency)}ms`, tone: 'default' })
  if (meta.fallback) chips.push({ label: `fallback: ${meta.fallback}`, tone: 'amber' })
  if (meta.error) chips.push({ label: 'error', tone: 'red' })
  if (meta.escalated) chips.push({ label: 'escalated', tone: 'amber' })

  if (chips.length === 0 && !meta.trace) return null

  return (
    <div className="mt-2 flex flex-wrap gap-1.5 items-center">
      {chips.map((c, i) => <Badge key={i} tone={c.tone}>{c.label}</Badge>)}
      {meta.trace && (
        <button onClick={() => setOpen(o => !o)}
                className="text-[11px] text-text-muted hover:text-accent-purple flex items-center gap-1">
          <ChevronDown className={`w-3 h-3 transition ${open ? 'rotate-180' : ''}`} />
          trace
        </button>
      )}
      {open && meta.trace && (
        <pre className="w-full mt-2 text-[11px] bg-bg-soft border border-border rounded p-2
                        overflow-x-auto text-text-muted">
          {JSON.stringify(meta.trace, null, 2)}
        </pre>
      )}
    </div>
  )
}
