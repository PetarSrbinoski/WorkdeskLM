'use client'

import React from "react"

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import type { ChatMode, Document } from '@/lib/types'
import { Send, Loader2, Settings2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'

interface ChatInputProps {
  onSend: (question: string, mode: ChatMode, topK: number, minScore: number, docId?: string) => Promise<void>
  documents: Document[]
  disabled?: boolean
}

export function ChatInput({ onSend, documents, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<ChatMode>('fast')
  const [topK, setTopK] = useState(5)
  const [minScore, setMinScore] = useState(0.5)
  const [docId, setDocId] = useState<string>('all')
  const [sending, setSending] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`
    }
  }, [input])

  const handleSubmit = async () => {
    if (!input.trim() || sending || disabled) return
    
    const question = input.trim()
    setInput('')
    setSending(true)
    
    try {
      await onSend(question, mode, topK, minScore, docId === 'all' ? undefined : docId)
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="border-t bg-background p-4">
      <Collapsible open={showSettings} onOpenChange={setShowSettings}>
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              className="w-full resize-none rounded-lg border bg-background px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-crimson/50 min-h-[48px] max-h-[150px]"
              rows={1}
              disabled={disabled || sending}
            />
          </div>
          
          <CollapsibleTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className={cn(showSettings && 'bg-accent')}
            >
              <Settings2 className="size-4" />
            </Button>
          </CollapsibleTrigger>
          
          <Button
            onClick={handleSubmit}
            disabled={!input.trim() || sending || disabled}
            className="bg-crimson hover:bg-crimson/90 text-white"
          >
            {sending ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </div>
        
        <CollapsibleContent className="pt-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-4 rounded-lg bg-accent/50">
            <div className="space-y-2">
              <Label className="text-xs">Mode</Label>
              <Select value={mode} onValueChange={(v) => setMode(v as ChatMode)}>
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fast">Fast</SelectItem>
                  <SelectItem value="quality">Quality</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs">Document</Label>
              <Select value={docId} onValueChange={setDocId}>
                <SelectTrigger className="h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Documents</SelectItem>
                  {documents.map((doc) => (
                    <SelectItem key={doc.id} value={doc.id}>
                      {doc.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs">Top K: {topK}</Label>
              <Slider
                value={[topK]}
                onValueChange={([v]) => setTopK(v)}
                min={1}
                max={20}
                step={1}
                className="py-2"
              />
            </div>
            
            <div className="space-y-2">
              <Label className="text-xs">Min Score: {minScore.toFixed(2)}</Label>
              <Slider
                value={[minScore]}
                onValueChange={([v]) => setMinScore(v)}
                min={0}
                max={1}
                step={0.05}
                className="py-2"
              />
            </div>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  )
}
