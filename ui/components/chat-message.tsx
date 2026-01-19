'use client'

import React from "react"

import { Badge } from '@/components/ui/badge'
import type { ChatMessage as ChatMessageType } from '@/lib/types'
import { cn } from '@/lib/utils'
import { AlertTriangle, Clock, Cpu } from 'lucide-react'

interface ChatMessageProps {
  message: ChatMessageType
}

function formatCitations(content: string): React.ReactNode {
  // Parse citation tags like [DOC=filename.pdf|PAGE=2|CHUNK=1]
  const parts = content.split(/(\[DOC=[^\]]+\])/g)
  
  return parts.map((part, index) => {
    const match = part.match(/\[DOC=([^|]+)\|PAGE=(\d+)\|CHUNK=(\d+)\]/)
    if (match) {
      const [, docName, page, chunk] = match
      return (
        <span
          key={index}
          className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-crimson/10 text-crimson text-xs font-medium"
          title={`${docName} - Page ${page}, Chunk ${chunk}`}
        >
          p{page}
        </span>
      )
    }
    return part
  })
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div
      className={cn(
        'flex',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'max-w-[80%] space-y-2',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-crimson text-white rounded-t-none rounded-b-lg rounded-l-lg'
              : 'bg-secondary text-secondary-foreground rounded-t-none rounded-b-lg rounded-r-lg'
          )}
        >
          {isUser ? message.content : formatCitations(message.content)}
        </div>
        
        {!isUser && (message.model_used || message.latency || message.abstained) && (
          <div className="flex flex-wrap gap-1.5 px-1">
            {message.abstained && (
              <Badge 
                variant="secondary" 
                className="gap-1 text-xs bg-amber-500/10 text-amber-600 dark:text-amber-400 border-0"
              >
                <AlertTriangle className="size-3" />
                Abstained
              </Badge>
            )}
            {message.model_used && (
              <Badge variant="secondary" className="gap-1 text-xs border-0">
                <Cpu className="size-3" />
                {message.model_used}
              </Badge>
            )}
            {message.mode_used && (
              <Badge variant="secondary" className="gap-1 text-xs border-0">
                {message.mode_used}
              </Badge>
            )}
            {message.latency && (
              <Badge variant="secondary" className="gap-1 text-xs border-0">
                <Clock className="size-3" />
                {message.latency.total_ms}ms
              </Badge>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
