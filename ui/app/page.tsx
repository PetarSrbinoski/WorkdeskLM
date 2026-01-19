'use client'

import { useState, useCallback, useEffect } from 'react'
import { LandingPage } from '@/components/landing-page'
import { Sidebar } from '@/components/sidebar'
import { ChatArea } from '@/components/chat-area'
import { SourcesPanel } from '@/components/sources-panel'
import { ErrorBanner } from '@/components/error-banner'
import { chat } from '@/lib/api'
import type { ChatMessage, ChatMode, Document, Citation } from '@/lib/types'
import { Button } from '@/components/ui/button'
import { Menu } from 'lucide-react'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'

export default function HomePage() {
  const [showChat, setShowChat] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [citations, setCitations] = useState<Citation[] | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [darkMode, setDarkMode] = useState(false)

  // Initialize dark mode from system preference on mount
  useEffect(() => {
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
    setDarkMode(isDark)
    if (isDark) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  const toggleDarkMode = () => {
    const newDarkMode = !darkMode
    setDarkMode(newDarkMode)
    if (newDarkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }

  const handleSend = useCallback(async (
    question: string,
    mode: ChatMode,
    topK: number,
    minScore: number,
    docId?: string
  ) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      timestamp: new Date(),
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
      }
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get response')
    } finally {
      setLoading(false)
    }
  }, [])

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

  // Show landing page if chat hasn't started
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
      {/* Desktop Sidebar */}
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

      {/* Mobile Sidebar */}
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

      {/* Main Content - Full width for chat */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header - Mobile only */}
        <header className="flex items-center justify-between px-4 py-3 border-b md:hidden">
          <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon">
                <Menu className="size-5" />
              </Button>
            </SheetTrigger>
          </Sheet>
          <span className="font-semibold">NotebookLM</span>
          <div className="w-10" /> {/* Spacer for alignment */}
        </header>

        {/* Chat Area */}
        <div className="flex-1 min-h-0">
          <ChatArea
            messages={messages}
            documents={documents}
            loading={loading}
            onSend={handleSend}
            onClear={handleClear}
            onCitationsChange={handleCitationsChange}
          />
        </div>
      </main>

      {/* Sources Panel - Now slides from left */}
      <SourcesPanel
        citations={citations}
        open={sourcesOpen}
        onOpenChange={setSourcesOpen}
      />

      {/* Error Banner */}
      {error && (
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
      )}
    </div>
  )
}
