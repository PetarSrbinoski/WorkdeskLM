'use client'

import {useRef, useEffect} from 'react'
import {ScrollArea} from '@/components/ui/scroll-area'
import {Button} from '@/components/ui/button'
import {ChatMessage} from '@/components/chat-message'
import {ChatInput} from '@/components/chat-input'
import {Skeleton} from '@/components/ui/skeleton'
import type {ChatMessage as ChatMessageType, ChatMode, Document, Citation} from '@/lib/types'
import {Trash2, MessageSquare, Upload, Plus} from 'lucide-react'
import {FlashcardsMessage} from '@/components/flashcards/message'

interface ChatAreaProps {
    messages: ChatMessageType[]
    documents: Document[]
    loading: boolean
    onSend: (question: string, mode: ChatMode, topK: number, minScore: number, docId?: string) => Promise<void>
    onClear: () => void
    onCitationsChange: (citations: Citation[] | null) => void

    onNewSession: () => Promise<void>

    selectedDocId: string
    onSelectedDocIdChange: (docId: string) => void
}

export function ChatArea({
                             messages,
                             documents,
                             loading,
                             onSend,
                             onClear,
                             onCitationsChange,
                             onNewSession,
                             selectedDocId,
                             onSelectedDocIdChange,
                         }: ChatAreaProps) {
    const scrollRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight
        }
    }, [messages])

    useEffect(() => {
        const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant')
        onCitationsChange(lastAssistantMessage?.citations ?? null)
    }, [messages, onCitationsChange])

    return (
        <div className="flex flex-col h-full max-h-screen overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b shrink-0">
                <div className="flex items-center gap-2">
                    <MessageSquare className="size-5 text-muted-foreground"/>
                    <h2 className="font-medium">Chat</h2>
                </div>

                <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={onNewSession} disabled={loading}>
                        <Plus className="size-4"/>
                        New chat
                    </Button>

                    {messages.length > 0 && (
                        <Button variant="ghost" size="sm" onClick={onClear} disabled={loading}>
                            <Trash2 className="size-4"/>
                            Clear
                        </Button>
                    )}
                </div>
            </div>

            <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                    <div className="p-4 space-y-4">
                        {messages.length === 0 && !loading && documents.length === 0 && (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <div className="size-16 rounded-full bg-accent flex items-center justify-center mb-4">
                                    <Upload className="size-8 text-muted-foreground"/>
                                </div>
                                <h3 className="font-medium mb-1">Upload a document first</h3>
                                <p className="text-sm text-muted-foreground max-w-sm">
                                    Use the left sidebar to upload a file, then ask questions in chat.
                                </p>
                            </div>
                        )}

                        {messages.length === 0 && !loading && documents.length > 0 && (
                            <div className="flex flex-col items-center justify-center py-12 text-center">
                                <div className="size-16 rounded-full bg-accent flex items-center justify-center mb-4">
                                    <MessageSquare className="size-8 text-muted-foreground"/>
                                </div>
                                <h3 className="font-medium mb-1">Start a conversation</h3>
                                <p className="text-sm text-muted-foreground max-w-sm">
                                    Ask questions about your uploaded documents. The AI will respond with citations when
                                    available.
                                </p>
                            </div>
                        )}

                        {messages.map((message) => {
                            if (message.flashcards?.length) {
                                return (
                                    <div key={message.id} className="flex justify-start">
                                        <div
                                            className="max-w-[80%] bg-secondary rounded-t-none rounded-b-lg rounded-r-lg px-4 py-3">
                                            <FlashcardsMessage cards={message.flashcards}/>
                                        </div>
                                    </div>
                                )
                            }
                            return <ChatMessage key={message.id} message={message}/>
                        })}

                        {loading && (
                            <div className="flex justify-start">
                                <div className="max-w-[80%] space-y-2">
                                    <div className="bg-secondary rounded-t-none rounded-b-lg rounded-r-lg px-4 py-3">
                                        <div className="space-y-2">
                                            <Skeleton className="h-4 w-[250px]"/>
                                            <Skeleton className="h-4 w-[200px]"/>
                                            <Skeleton className="h-4 w-[180px]"/>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </div>

            <div className="shrink-0">
                <ChatInput
                    onSend={onSend}
                    documents={documents}
                    disabled={loading}
                    selectedDocId={selectedDocId}
                    onSelectedDocIdChange={onSelectedDocIdChange}
                />
            </div>
        </div>
    )
}
