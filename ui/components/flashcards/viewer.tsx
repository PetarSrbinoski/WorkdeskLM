'use client'

import * as React from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import type { Flashcard } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'
import Stack from './stack'
import { FlipCard } from './flip-card'

function PrettyCard({
  card,
  flipped,
  onToggle,
}: {
  card: Flashcard
  flipped: boolean
  onToggle: () => void
}) {
  return (
    <div className="w-full h-full rounded-3xl overflow-hidden">
      <div className="w-full h-full bg-gradient-to-br from-background to-accent/30 p-4">
        <div className="w-full h-full rounded-2xl border bg-background/80 backdrop-blur-sm shadow-sm">
          <FlipCard
            front={
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="border-0">
                    Question
                  </Badge>
                  <span className="text-xs text-muted-foreground">tap to flip</span>
                </div>

                <div className="text-xl md:text-2xl font-semibold leading-snug tracking-tight">
                  {card.q}
                </div>

                <div className="pt-2 text-xs text-muted-foreground">
                  Tip: click anywhere on the card to flip
                </div>
              </div>
            }
            back={
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Badge variant="secondary" className="border-0">
                    Answer
                  </Badge>
                  <span className="text-xs text-muted-foreground">tap to flip</span>
                </div>

                <div className="text-base md:text-lg leading-relaxed text-foreground/90 whitespace-pre-wrap">
                  {card.a}
                </div>

                <div className="pt-2 text-xs text-muted-foreground">
                  Tip: click anywhere on the card to flip back
                </div>
              </div>
            }
            flipped={flipped}
            onToggle={onToggle}
            className="h-full"
          />
        </div>
      </div>
    </div>
  )
}

export function FlashcardsViewer({
  open,
  cards,
  onClose,
}: {
  open: boolean
  cards: Flashcard[]
  onClose: () => void
}) {
  const [index, setIndex] = React.useState(0)
  const [flipped, setFlipped] = React.useState(false)

  React.useEffect(() => {
    if (!open) return
    setIndex(0)
    setFlipped(false)
  }, [open])

  const hasCards = cards.length > 0

  const prev = () => {
    if (!hasCards) return
    setFlipped(false)
    setIndex((i) => (i - 1 + cards.length) % cards.length)
  }

  const next = () => {
    if (!hasCards) return
    setFlipped(false)
    setIndex((i) => (i + 1) % cards.length)
  }

  // Build a stack of up to 6 cards where the LAST is the "top" (current) card.
  const stackNodes = React.useMemo(() => {
    if (!hasCards) return []
    const take = Math.min(6, cards.length)
    const arr: Flashcard[] = []

    // previous cards behind
    for (let k = take - 1; k >= 1; k--) {
      const idx = (index - k + cards.length) % cards.length
      arr.push(cards[idx])
    }
    // current card on top
    arr.push(cards[index])

    return arr.map((c, idx) => {
      const isTop = idx === arr.length - 1
      return (
        <PrettyCard
          key={`${index}-${idx}-${c.q.slice(0, 12)}`}
          card={c}
          flipped={isTop ? flipped : false}
          onToggle={() => {
            if (isTop) setFlipped((f) => !f)
          }}
        />
      )
    })
  }, [cards, hasCards, index, flipped])

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        >
          {/* backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/50"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* panel */}
          <motion.div
            className="relative w-[min(900px,94vw)]"
            initial={{ scale: 0.95, opacity: 0, y: 14 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.97, opacity: 0, y: 10 }}
            transition={{ type: 'spring', stiffness: 260, damping: 24 }}
          >
            {/* top bar */}
            <div className="flex items-center justify-between px-2 mb-4">
              <div className="text-sm text-white/90">
                {hasCards ? `${index + 1} / ${cards.length}` : '0 / 0'}
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="text-white hover:bg-white/10"
              >
                <X className="size-5" />
              </Button>
            </div>

            {/* stack stage */}
            <div className="relative mx-auto w-[min(540px,90vw)] h-[min(540px,70vh)]">
              <Stack
                cards={stackNodes}
                randomRotation
                sendToBackOnClick={false}
                mobileClickOnly
                disableDrag
                sensitivity={999999}
                onClickStack={() => setFlipped((f) => !f)}
                animationConfig={{ stiffness: 260, damping: 22 }}
              />
            </div>

            {/* controls */}
            <div className="flex items-center justify-center gap-3 mt-6">
              <Button variant="secondary" onClick={prev} disabled={!hasCards}>
                <ChevronLeft className="size-4 mr-1" />
                Previous
              </Button>

              <Button
                variant="secondary"
                onClick={() => setFlipped((f) => !f)}
                disabled={!hasCards}
              >
                Flip
              </Button>

              <Button variant="secondary" onClick={next} disabled={!hasCards}>
                Next
                <ChevronRight className="size-4 ml-1" />
              </Button>
            </div>

            <div className="mt-3 text-center text-xs text-white/70">
              Tip: click the stack or press “Flip” to reveal the answer.
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
