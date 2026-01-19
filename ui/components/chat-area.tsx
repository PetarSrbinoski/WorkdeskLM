'use client'

import { useRef, useEffect } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { ChatMessage } from '@/components/chat-message'
import { ChatInput } from '@/components/chat-input'
import { Skeleton } from '@/components/ui/skeleton'
import type { ChatMessage as ChatMessageType, ChatMode, Document, Citation } from '@/lib/types'
import { Trash2, MessageSquare, Upload } from 'lucide-react'

interface ChatAreaProps {
  messages: ChatMessageType[]
  documents: Document[]
  loading: boolean
  onSend: (question: string, mode: ChatMode, topK: number, minScore: number, docId?: string) => Promise<void>
  onClear: () => void
  onCitationsChange: (citations: Citation[] | null) => void
}

export function ChatArea({
  messages,
  documents,
  loading,
  onSend,
  onClear,
  onCitationsChange,
}: ChatAreaProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // Update citations when messages change
  useEffect(() => {
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant')
    onCitationsChange(lastAssistantMessage?.citations ?? null)
  }, [messages, onCitationsChange])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <div className="flex items-center gap-2">
          <MessageSquare className="size-5 text-muted-foreground" />
          <h2 className="font-medium">Chat</h2>
        </div>
        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={onClear}>
            <Trash2 className="size-4" />
            Clear
          </Button>
        )}
      </div>
      
      <ScrollArea className="flex-1" ref={scrollRef}>
        <div className="p-4 space-y-4">
          {messages.length === 0 && !loading && documents.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="size-16 rounded-full bg-accent flex items-center justify-center mb-4">
                <Upload className="size-8 text-muted-foreground" />
              </div>
              <h3 className="font-medium mb-1">Upload a document first</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Use the sidebar to upload a PDF, TXT, or Markdown file. Once uploaded, you can start asking questions about your documents.
              </p>
            </div>
          )}
          
          {messages.length === 0 && !loading && documents.length > 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="size-16 rounded-full bg-accent flex items-center justify-center mb-4">
                <MessageSquare className="size-8 text-muted-foreground" />
              </div>
              <h3 className="font-medium mb-1">Start a conversation</h3>
              <p className="text-sm text-muted-foreground max-w-sm">
                Ask questions about your uploaded documents. The AI will search through your knowledge base to provide answers with citations.
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          
          {loading && (
            <div className="flex justify-start">
              <div className="max-w-[80%] space-y-2">
                <div className="bg-secondary rounded-t-none rounded-b-lg rounded-r-lg px-4 py-3">
                  <div className="space-y-2">
                    <Skeleton className="h-4 w-[250px]" />
                    <Skeleton className="h-4 w-[200px]" />
                    <Skeleton className="h-4 w-[180px]" />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
      
      <ChatInput onSend={onSend} documents={documents} disabled={loading} />
    </div>
  )
}
