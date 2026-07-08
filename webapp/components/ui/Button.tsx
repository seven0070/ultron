import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'ghost' | 'outline'

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
}

export const Button = forwardRef<HTMLButtonElement, Props>(
  ({ className, variant = 'primary', ...rest }, ref) => (
    <button
      ref={ref}
      className={cn(
        variant === 'primary' && 'btn-primary',
        variant === 'ghost'   && 'btn-ghost',
        variant === 'outline' && 'btn-outline',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        className,
      )}
      {...rest}
    />
  ),
)
Button.displayName = 'Button'
