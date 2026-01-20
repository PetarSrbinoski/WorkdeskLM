// FILE: components/sidebar.tsx
'use client'

import { useEffect, useState, useCallback } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { HealthStatus } from '@/components/health-status'
import { FileUpload } from '@/components/file-upload'
import { DocumentCard } from '@/components/document-card'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { getDocuments, ingestDocument, deleteDocument } from '@/lib/api'
import type { Document } from '@/lib/types'
import { BookOpen, Moon, Sun } from 'lucide-react'

interface SidebarProps {
  onError: (message: string) => void
  onDocumentsChange?: (documents: Document[]) => void
  citationCount?: number
  onSourcesClick?: () => void
  darkMode?: boolean
  onToggleDarkMode?: () => void
  onGoHome?: () => void
}

export function Sidebar({
  onError,
  onDocumentsChange,
  citationCount = 0,
  onSourcesClick,
  darkMode = false,
  onToggleDarkMode,
  onGoHome,
}: SidebarProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await getDocuments()
      setDocuments(data.documents)
      onDocumentsChange?.(data.documents)
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to fetch documents')
    } finally {
      setLoading(false)
    }
  }, [onError, onDocumentsChange])

  useEffect(() => {
    fetchDocuments()
  }, [fetchDocuments])

  const handleUpload = async (file: File) => {
    try {
      await ingestDocument(file)
      await fetchDocuments()
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to upload document')
    }
  }

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId)
      await fetchDocuments()
    } catch (err) {
      onError(err instanceof Error ? err.message : 'Failed to delete document')
    }
  }

  return (
    <aside className="w-100 border-r bg-sidebar flex flex-col h-screen">
      {/* Header with logo and theme toggle */}
      <div className="p-4 border-b shrink-0">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={onGoHome}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <div className="size-8 rounded-lg bg-crimson flex items-center justify-center">
              <BookOpen className="size-4 text-white" />
            </div>
            <div className="text-left">
              <h1 className="text-sm font-semibold">WorkdeskLM</h1>
              <p className="text-xs text-muted-foreground">Local-first AI</p>
            </div>
          </button>
          {onToggleDarkMode && (
            <Button variant="ghost" size="icon" onClick={onToggleDarkMode} className="shrink-0">
              {darkMode ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
          )}
        </div>
      </div>

      {/* Sources Button */}
      {onSourcesClick && (
        <div className="px-4 pt-4 shrink-0">
          <Button
            variant="outline"
            className="w-full justify-start gap-2 bg-transparent"
            onClick={onSourcesClick}
          >
            <BookOpen className="size-4" />
            <span className="flex-1 text-left">Sources</span>
            {citationCount > 0 && (
              <Badge variant="secondary" className="border-0 px-1.5">
                {citationCount}
              </Badge>
            )}
          </Button>
        </div>
      )}

      {/* Scrollable content */}
      <ScrollArea className="flex-1 min-h-0">
        <div className="p-4 space-y-4">
          <HealthStatus />

          <div>
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Upload Document
            </h2>
            <FileUpload onUpload={handleUpload} />
          </div>

          <div>
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-3">
              Documents ({documents.length})
            </h2>

            {loading ? (
              <div className="space-y-2">
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </div>
            ) : documents.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                No documents yet. Upload one to get started.
              </p>
            ) : (
              <div className="space-y-2 pr-1">
                {documents.map((doc) => (
                  <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
                ))}
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
    </aside>
  )
}
