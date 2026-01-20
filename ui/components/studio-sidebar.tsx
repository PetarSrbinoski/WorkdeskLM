'use client'

import { useEffect, useMemo, useState } from 'react'
import type { Document, Flashcard } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { AlertTriangle, FileText, Layers, Sparkles } from 'lucide-react'
import { studioBrief, studioFlashcards, summarizeSession, getDocuments } from '@/lib/api'

const DOC_STORAGE_KEY = 'workdesklm_doc_id'

interface StudioSidebarProps {
  sessionId: string | null

  documents: Document[]
  onDocumentsChange: (docs: Document[]) => void

  selectedDocId: string // 'all' or doc id
  onSelectedDocIdChange: (id: string) => void

  // push results into chat
  onBriefToChat: (brief: string) => void
  onSummaryToChat: (summary: string) => void
  onFlashcardsToChat: (cards: Flashcard[]) => void

  onNewSession: () => Promise<void>

  // NEW: disable summarize unless there is chat
  hasChat: boolean

  disabled?: boolean
}

export function StudioSidebar({
  sessionId,
  documents,
  onDocumentsChange,
  selectedDocId,
  onSelectedDocIdChange,
  onBriefToChat,
  onSummaryToChat,
  onFlashcardsToChat,
  onNewSession,
  hasChat,
  disabled = false,
}: StudioSidebarProps) {
  const [flashcardCount, setFlashcardCount] = useState(8)
  const [loading, setLoading] = useState<null | 'brief' | 'flashcards' | 'summarize' | 'docs' | 'newchat'>(null)
  const [error, setError] = useState<string | null>(null)

  const effectiveDocId = useMemo(
    () => (selectedDocId === 'all' ? undefined : selectedDocId),
    [selectedDocId]
  )

  useEffect(() => {
    try {
      const stored = localStorage.getItem(DOC_STORAGE_KEY)
      if (stored && stored !== selectedDocId) onSelectedDocIdChange(stored)
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setDocAndPersist = (id: string) => {
    onSelectedDocIdChange(id)
    try {
      localStorage.setItem(DOC_STORAGE_KEY, id)
    } catch {
      // ignore
    }
  }

  const refreshDocs = async () => {
    setError(null)
    setLoading('docs')
    try {
      const res = await getDocuments()
      onDocumentsChange(res.documents)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to refresh documents')
    } finally {
      setLoading(null)
    }
  }

  const runBrief = async () => {
    setError(null)
    setLoading('brief')
    try {
      const res = await studioBrief({
        doc_id: effectiveDocId,
        question: 'Summarize…',
        mode: 'quality',
      })
      onBriefToChat(res.brief)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate brief')
    } finally {
      setLoading(null)
    }
  }

  const runSummarizeSession = async () => {
    if (!sessionId) {
      setError('No active session.')
      return
    }
    setError(null)
    setLoading('summarize')
    try {
      const res = await summarizeSession(sessionId)
      onSummaryToChat(res.summary)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to summarize session')
    } finally {
      setLoading(null)
    }
  }

  const runFlashcards = async () => {
    setError(null)
    setLoading('flashcards')
    try {
      const res = await studioFlashcards({
        doc_id: effectiveDocId,
        count: flashcardCount,
        mode: 'quality',
      })
      onFlashcardsToChat(res.cards ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate flashcards')
    } finally {
      setLoading(null)
    }
  }

  const runNewChat = async () => {
    setError(null)
    setLoading('newchat')
    try {
      await onNewSession()
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create session')
    } finally {
      setLoading(null)
    }
  }

  return (
    <aside className="w-92 border-l bg-sidebar flex flex-col h-full">
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <div className="text-left">
            <h2 className="text-sm font-semibold">Studio</h2>
            <p className="text-xs text-muted-foreground">Briefs, flashcards, session summary</p>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-5">
          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm">
              <div className="flex items-start gap-2">
                <AlertTriangle className="size-4 mt-0.5 text-destructive" />
                <div className="text-destructive">{error}</div>
              </div>
            </div>
          )}

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-xs">Document scope (optional)</Label>
              <Button variant="ghost" size="sm" onClick={refreshDocs} disabled={disabled || loading === 'docs'}>
                {loading === 'docs' ? 'Refreshing…' : 'Refresh'}
              </Button>
            </div>

            <Select value={selectedDocId} onValueChange={setDocAndPersist}>
              <SelectTrigger className="h-10" disabled={disabled}>
                <SelectValue placeholder="All documents" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All documents</SelectItem>
                {documents.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <p className="text-xs text-muted-foreground">
              Applies to chat + Studio actions.
            </p>
          </div>

          <div className="grid gap-2">
            <Button
              variant="outline"
              className="justify-start gap-2"
              onClick={runBrief}
              disabled={disabled || loading !== null}
            >
              <FileText className="size-4" />
              Brief
              {loading === 'brief' && <span className="ml-auto text-xs text-muted-foreground">Loading…</span>}
            </Button>

            <div className="rounded-lg border p-3 space-y-3">
              <div className="flex items-center gap-2">
                <Layers className="size-4 text-muted-foreground" />
                <div className="text-sm font-medium">Flashcards</div>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-xs">Count</Label>
                  <Badge variant="secondary" className="border-0">
                    {flashcardCount}
                  </Badge>
                </div>
                <Slider
                  value={[flashcardCount]}
                  onValueChange={([v]) => setFlashcardCount(v)}
                  min={3}
                  max={20}
                  step={1}
                  className="py-2"
                />
              </div>

              <Button
                className="w-full justify-start gap-2"
                onClick={runFlashcards}
                disabled={disabled || loading !== null}
              >
                <Sparkles className="size-4" />
                Generate
                {loading === 'flashcards' && <span className="ml-auto text-xs text-muted-foreground">Loading…</span>}
              </Button>
            </div>

            <Button
              variant="outline"
              className="justify-start gap-2"
              onClick={runSummarizeSession}
              disabled={disabled || loading !== null || !sessionId || !hasChat}
            >
              <FileText className="size-4" />
              Summarize session
              {loading === 'summarize' && <span className="ml-auto text-xs text-muted-foreground">Loading…</span>}
            </Button>

            {!hasChat && (
              <p className="text-xs text-muted-foreground">
                Send at least one message to enable session summary.
              </p>
            )}
          </div>
        </div>
      </ScrollArea>
    </aside>
  )
}
