'use client'

import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import rehypeSanitize from 'rehype-sanitize'

import { Badge } from '@/components/ui/badge'
import type { ChatMessage as ChatMessageType } from '@/lib/types'
import { cn } from '@/lib/utils'
import { AlertTriangle, Clock, Cpu } from 'lucide-react'

interface ChatMessageProps {
  message: ChatMessageType
}

const citeRe = /\[DOC=([^|]+)\|PAGE=(\d+)\|CHUNK=(\d+)\]/g

function splitWithCites(text: string): React.ReactNode[] {
  const out: React.ReactNode[] = []
  let last = 0
  let m: RegExpExecArray | null

  while ((m = citeRe.exec(text)) !== null) {
    const start = m.index
    if (start > last) out.push(text.slice(last, start))

    const docName = m[1]
    const page = m[2]
    const chunk = m[3]

    out.push(
      <span
        key={`${docName}-${page}-${chunk}-${start}`}
        className="inline-flex items-center px-1.5 py-0.5 mx-0.5 rounded bg-crimson/10 text-crimson text-xs font-medium align-baseline"
        title={`${docName} - Page ${page}, Chunk ${chunk}`}
      >
        p{page}
      </span>
    )

    last = start + m[0].length
  }

  if (last < text.length) out.push(text.slice(last))
  return out
}

function Md({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      rehypePlugins={[rehypeRaw, rehypeSanitize]} // remove both if you don't need raw HTML
      components={{
        // Replace plain text nodes so citations become inline badges
        text({ children }) {
          const txt = String(children)
          return <>{splitWithCites(txt)}</>
        },

        // Basic nice defaults (no "AI-looking" heavy styling)
        a({ children, href, ...props }) {
          return (
            <a
              {...props}
              href={href}
              target="_blank"
              rel="noreferrer"
              className="underline underline-offset-2"
            >
              {children}
            </a>
          )
        },
        code({ inline, children, ...props }) {
          if (inline) {
            return (
              <code
                {...props}
                className="px-1 py-0.5 rounded bg-black/5 dark:bg-white/10"
              >
                {children}
              </code>
            )
          }
          return (
            <pre className="p-3 rounded bg-black/5 dark:bg-white/10 overflow-x-auto">
              <code {...props}>{children}</code>
            </pre>
          )
        },
        ul({ children, ...props }) {
          return (
            <ul {...props} className="list-disc pl-5 space-y-1">
              {children}
            </ul>
          )
        },
        ol({ children, ...props }) {
          return (
            <ol {...props} className="list-decimal pl-5 space-y-1">
              {children}
            </ol>
          )
        },
        p({ children }) {
          return <p className="whitespace-pre-wrap">{children}</p>
        }
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[80%] space-y-2', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'bg-crimson text-white rounded-t-none rounded-b-lg rounded-l-lg'
              : 'bg-secondary text-secondary-foreground rounded-t-none rounded-b-lg rounded-r-lg'
          )}
        >
          {isUser ? (
            <Md content={message.content} />
          ) : (
            <Md content={message.content} />
          )}
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
