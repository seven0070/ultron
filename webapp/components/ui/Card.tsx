import { type HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('glass rounded-xl p-4', className)} {...rest} />
}
export function CardTitle({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('font-semibold text-sm text-text-DEFAULT', className)} {...rest} />
}
