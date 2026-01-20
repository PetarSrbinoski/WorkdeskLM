'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export function FlipCard({
  front,
  back,
  flipped,
  onToggle,
  className,
}: {
  front: React.ReactNode
  back: React.ReactNode
  flipped: boolean
  onToggle: () => void
  className?: string
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn('w-full h-full [perspective:1000px] text-left', className)}
    >
      <div
        className={cn(
          'relative w-full h-full duration-500 [transform-style:preserve-3d]',
          flipped ? '[transform:rotateY(180deg)]' : ''
        )}
      >
        <div className="absolute inset-0 rounded-2xl border bg-background p-5 shadow-sm [backface-visibility:hidden]">
          <div className="text-xs text-muted-foreground mb-2">Question</div>
          <div className="text-sm leading-relaxed">{front}</div>
          <div className="absolute bottom-3 right-4 text-xs text-muted-foreground">
            click to flip
          </div>
        </div>

        <div className="absolute inset-0 rounded-2xl border bg-background p-5 shadow-sm [transform:rotateY(180deg)] [backface-visibility:hidden]">
          <div className="text-xs text-muted-foreground mb-2">Answer</div>
          <div className="text-sm leading-relaxed">{back}</div>
          <div className="absolute bottom-3 right-4 text-xs text-muted-foreground">
            click to flip
          </div>
        </div>
      </div>
    </button>
  )
}
