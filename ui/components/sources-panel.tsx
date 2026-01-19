'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import type { Citation } from '@/lib/types'
import { BookOpen, ChevronDown, Copy, Check, X, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

interface SourcesPanelProps {
  citations: Citation[] | null
  open: boolean
  onOpenChange: (open: boolean) => void
}

function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <Collapsible open={expanded} onOpenChange={setExpanded}>
      <div className="border rounded-lg overflow-hidden">
        <CollapsibleTrigger asChild>
          <button className="w-full p-3 flex items-start gap-3 hover:bg-accent/50 transition-colors text-left">
            <div className="size-6 rounded bg-crimson/10 text-crimson flex items-center justify-center text-xs font-medium shrink-0">
              {index + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <FileText className="size-3 text-muted-foreground shrink-0" />
                <span className="text-sm font-medium truncate">{citation.doc_name}</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span>Page {citation.page_number}</span>
                <span>·</span>
                <span>Chunk {citation.chunk_index}</span>
                <span>·</span>
                <Badge variant="secondary" className="text-xs border-0 px-1.5">
                  {citation.score.toFixed(3)}
                </Badge>
              </div>
            </div>
            <ChevronDown 
              className={cn(
                "size-4 text-muted-foreground transition-transform shrink-0",
                expanded && "rotate-180"
              )} 
            />
          </button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div className="px-3 pb-3 pt-0">
            <div className="bg-muted/50 rounded p-3 text-sm text-muted-foreground leading-relaxed border-l-2 border-crimson/30">
              {citation.quote}
            </div>
          </div>
        </CollapsibleContent>
      </div>
    </Collapsible>
  )
}

export function SourcesPanel({ citations, open, onOpenChange }: SourcesPanelProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!citations) return
    
    const formatted = citations
      .map((c) => `- ${c.doc_name} p${c.page_number} chunk${c.chunk_index} (score=${c.score.toFixed(3)})`)
      .join('\n')
    
    await navigator.clipboard.writeText(formatted)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-full sm:max-w-md p-0 flex flex-col">
        <SheetHeader className="p-4 border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="size-5 text-muted-foreground" />
              <SheetTitle>Sources</SheetTitle>
              {citations && citations.length > 0 && (
                <Badge variant="secondary" className="border-0">
                  {citations.length}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-1">
              {citations && citations.length > 0 && (
                <Button variant="ghost" size="sm" onClick={handleCopy}>
                  {copied ? (
                    <>
                      <Check className="size-4" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="size-4" />
                      Copy
                    </>
                  )}
                </Button>
              )}
              <Button variant="ghost" size="icon-sm" onClick={() => onOpenChange(false)}>
                <X className="size-4" />
              </Button>
            </div>
          </div>
        </SheetHeader>
        
        <ScrollArea className="flex-1">
          <div className="p-4 space-y-3">
            {!citations || citations.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="size-12 rounded-full bg-accent flex items-center justify-center mb-4">
                  <BookOpen className="size-6 text-muted-foreground" />
                </div>
                <h3 className="font-medium mb-1">No sources yet</h3>
                <p className="text-sm text-muted-foreground max-w-xs">
                  Ask a question and relevant sources will appear here.
                </p>
              </div>
            ) : (
              citations.map((citation, index) => (
                <CitationCard 
                  key={`${citation.chunk_id}-${index}`} 
                  citation={citation} 
                  index={index} 
                />
              ))
            )}
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  )
}

// Trigger button to show in the main UI
export function SourcesTrigger({ 
  citationCount, 
  onClick 
}: { 
  citationCount: number
  onClick: () => void 
}) {
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onClick}
      className="gap-2 bg-transparent"
    >
      <BookOpen className="size-4" />
      Sources
      {citationCount > 0 && (
        <Badge variant="secondary" className="border-0 px-1.5">
          {citationCount}
        </Badge>
      )}
    </Button>
  )
}
