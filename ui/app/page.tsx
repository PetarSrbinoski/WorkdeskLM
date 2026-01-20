'use client'

import { useState, useCallback } from 'react'
import { LandingPage } from '@/components/landing-page'
import { Sidebar } from '@/components/sidebar'
import { StudioSidebar } from '@/components/studio-sidebar'
import { ChatArea } from '@/components/chat-area'
import { SourcesPanel } from '@/components/sources-panel'
import { ErrorBanner } from '@/components/error-banner'
import { chat } from '@/lib/api'
import type { ChatMessage, ChatMode, Document, Citation, Flashcard } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Menu, Sparkles } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { useSession } from '@/hooks/use-session'
import { useEffect } from 'react'

export default function HomePage() {
  const [showChat, setShowChat] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [citations, setCitations] = useState<Citation[] | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [sidebarOpen, setSidebarOpen] = useState(false) // left (mobile)
  const [studioOpen, setStudioOpen] = useState(false)   // right (mobile)

  const [darkMode, setDarkMode] = useState(true)

  const [selectedDocId, setSelectedDocId] = useState<string>('all')

  const { sessionId, initializing, createNewSession } = useSession()

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    if (newDarkMode) document.documentElement.classList.add('dark')
    else document.documentElement.classList.remove('dark')
  }

  useEffect(() => {
  document.documentElement.classList.add('dark')
}, [])

  const handleSend = useCallback(async (
    question: string,
    mode: ChatMode,
    topK: number,
    minScore: number,
    docId?: string
  ) => {
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      timestamp: new Date(),
      kind: 'text',
    }
    setMessages(prev => [...prev, userMessage])
    setLoading(true)
    setError(null)

    try {
      const response = await chat({
        question,
        mode,
        top_k: topK,
        min_score: minScore,
        doc_id: docId,
        session_id: sessionId ?? undefined,
      })

      const assistantMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        citations: response.citations,
        latency: response.latency,
        model_used: response.model_used,
        mode_used: response.mode_used,
        abstained: response.abstained,
        kind: 'text',
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get response')
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  const handleClear = useCallback(() => {
    setMessages([])
    setCitations(null)
  }, [])

  const handleCitationsChange = useCallback((newCitations: Citation[] | null) => {
    setCitations(newCitations)
  }, [])

  const handleDocumentsChange = useCallback((docs: Document[]) => {
    setDocuments(docs)
  }, [])

  const handleError = useCallback((message: string) => {
    setError(message)
  }, [])

  const handleNewSession = useCallback(async () => {
    await createNewSession()
    setMessages([])
    setCitations(null)
  }, [createNewSession])

  const pushAssistantText = useCallback((title: string, body: string) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: `**${title}**\n\n${body}`,
      timestamp: new Date(),
      kind: 'text',
    }
    setMessages(prev => [...prev, msg])
  }, [])

  const pushFlashcards = useCallback((cards: Flashcard[]) => {
    const msg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: 'Click here for flashcards',
      timestamp: new Date(),
      kind: 'flashcards',
      flashcards: cards,
    }
    setMessages(prev => [...prev, msg])
  }, [])

  if (!showChat) {
    return (
      <LandingPage
        onStart={() => setShowChat(true)}
        darkMode={darkMode}
        onToggleDarkMode={toggleDarkMode}
      />
    )
  }

  return (
    <div className="h-screen flex bg-background">
      {/* LEFT SIDEBAR (desktop) */}
      <div className="hidden md:block">
        <Sidebar
          onError={handleError}
          onDocumentsChange={handleDocumentsChange}
          citationCount={citations?.length ?? 0}
          onSourcesClick={() => setSourcesOpen(true)}
          darkMode={darkMode}
          onToggleDarkMode={toggleDarkMode}
          onGoHome={() => setShowChat(false)}
        />
      </div>

      {/* LEFT SIDEBAR (mobile) */}
      <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
        <SheetContent side="left" className="p-0 w-72">
          <Sidebar
            onError={handleError}
            onDocumentsChange={handleDocumentsChange}
            citationCount={citations?.length ?? 0}
            onSourcesClick={() => {
              setSidebarOpen(false)
              setSourcesOpen(true)
            }}
            darkMode={darkMode}
            onToggleDarkMode={toggleDarkMode}
            onGoHome={() => {
              setSidebarOpen(false)
              setShowChat(false)
            }}
          />
        </SheetContent>
      </Sheet>

      {/* CHAT (center) */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Mobile header with left + right toggles */}
        <header className="flex items-center justify-between px-4 py-3 border-b md:hidden">
          <div className="flex items-center gap-2">
            <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon">
                  <Menu className="size-5" />
                </Button>
              </SheetTrigger>
            </Sheet>

            <span className="font-semibold">WorkdeskLM</span>
          </div>

          <Sheet open={studioOpen} onOpenChange={setStudioOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" aria-label="Open Studio">
                <Sparkles className="size-5" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="p-0 w-[380px]">
              <StudioSidebar
                sessionId={sessionId}
                documents={documents}
                onDocumentsChange={handleDocumentsChange}
                selectedDocId={selectedDocId}
                onSelectedDocIdChange={setSelectedDocId}
                onBriefToChat={(brief) => pushAssistantText('Brief', brief)}
                onSummaryToChat={(summary) => pushAssistantText('Session summary', summary)}
                onFlashcardsToChat={(cards) => pushFlashcards(cards)}
                onNewSession={handleNewSession}
                hasChat={messages.length > 0}
                disabled={loading || initializing}
              />
            </SheetContent>
          </Sheet>
        </header>

        <div className="flex-1 min-h-0">
          <ChatArea
            messages={messages}
            documents={documents}
            loading={loading || initializing}
            onSend={handleSend}
            onClear={handleClear}
            onCitationsChange={handleCitationsChange}
            onNewSession={handleNewSession}
            selectedDocId={selectedDocId}
            onSelectedDocIdChange={setSelectedDocId}
          />
        </div>
      </main>

      {/* RIGHT STUDIO SIDEBAR (desktop) */}
      <div className="hidden md:block">
        <StudioSidebar
          sessionId={sessionId}
          documents={documents}
          onDocumentsChange={handleDocumentsChange}
          selectedDocId={selectedDocId}
          onSelectedDocIdChange={setSelectedDocId}
          onBriefToChat={(brief) => pushAssistantText('Brief', brief)}
          onSummaryToChat={(summary) => pushAssistantText('Session summary', summary)}
          onFlashcardsToChat={(cards) => pushFlashcards(cards)}
          onNewSession={handleNewSession}
          hasChat={messages.length > 0}
          disabled={loading || initializing}
        />
      </div>

      {/* Sources Panel */}
      <SourcesPanel citations={citations} open={sourcesOpen} onOpenChange={setSourcesOpen} />

      {/* Error Banner */}
      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
    </div>
  )
}
