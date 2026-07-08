'use client'
import { Sparkles, BookOpen, GitBranch, Wrench, Brain, Layers } from 'lucide-react'

export default function QuickActions({ onPick }: { onPick: (q: string) => void }) {
  const items = [
    { icon: Brain,     label: 'What can you do?',
      query: 'What are all your capabilities? Give me the highlights.' },
    { icon: Sparkles,  label: 'Try fusion',
      query: 'fuse: Explain how black holes work, in one paragraph a 10-year-old would understand.' },
    { icon: BookOpen,  label: 'Learn something',
      query: 'learn this: Monad-Ultron is a portable USB-based cognitive AI with 82 organs.' },
    { icon: Layers,    label: 'Show your organs',
      query: 'What are your cognitive organs? Give me a brief overview by category.' },
    { icon: GitBranch, label: 'Evolve a plugin',
      query: 'evolve: add a plugin that reports the current time and time zone' },
    { icon: Wrench,    label: 'Run a tool',
      query: 'run tool filesystem op=list path=.' },
  ]
  return (
    <div className="border-t border-border-soft glass px-4 py-3">
      <div className="max-w-3xl mx-auto flex gap-2 overflow-x-auto pb-1">
        {items.map(it => (
          <button
            key={it.label}
            onClick={() => onPick(it.query)}
            className="flex-shrink-0 flex items-center gap-2 px-3 py-2 rounded-lg
                       border border-border text-xs text-text-soft hover:text-text-DEFAULT
                       hover:border-accent-purple/50 hover:bg-bg-hover transition"
          >
            <it.icon className="w-3.5 h-3.5" />
            {it.label}
          </button>
        ))}
      </div>
    </div>
  )
}
