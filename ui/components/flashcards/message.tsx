'use client'

import * as React from 'react'
import type { Flashcard } from '@/lib/types'
import { FlashcardsViewer } from './viewer'

export function FlashcardsMessage({ cards }: { cards: Flashcard[] }) {
  const [open, setOpen] = React.useState(false)

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="w-full text-left">
        <div className="text-sm font-medium underline underline-offset-4">
          Click here for flashcards
        </div>
        <div className="text-xs text-muted-foreground mt-1">
          {cards.length} cards • opens study mode
        </div>
      </button>

      <FlashcardsViewer open={open} cards={cards} onClose={() => setOpen(false)} />
    </>
  )
}
