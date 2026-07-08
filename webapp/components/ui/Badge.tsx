import { cn } from '@/lib/utils'

export function Badge({
  children, tone = 'default', className,
}: {
  children: React.ReactNode
  tone?: 'default'|'purple'|'blue'|'green'|'amber'|'red'
  className?: string
}) {
  const tones = {
    default: 'bg-bg-hover text-text-soft border-border',
    purple:  'bg-accent-purple/15 text-accent-purple border-accent-purple/30',
    blue:    'bg-accent-blue/15   text-accent-blue   border-accent-blue/30',
    green:   'bg-accent-green/15  text-accent-green  border-accent-green/30',
    amber:   'bg-accent-amber/15  text-accent-amber  border-accent-amber/30',
    red:     'bg-accent-red/15    text-accent-red    border-accent-red/30',
  } as const
  return (
    <span className={cn(
      'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border',
      tones[tone], className,
    )}>
      {children}
    </span>
  )
}
