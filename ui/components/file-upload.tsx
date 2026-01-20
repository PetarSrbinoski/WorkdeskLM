'use client'

import React from "react"

import { useState, useCallback } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, Loader2, FileUp } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>
  disabled?: boolean
}

export function FileUpload({ onUpload, disabled }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleFile = async (file: File) => {
    if (!file) return
    
    const validTypes = ['application/pdf', 'text/plain', 'text/markdown']
    const validExtensions = ['.pdf', '.txt', '.md']
    const ext = file.name.toLowerCase().slice(file.name.lastIndexOf('.'))
    
    if (!validTypes.includes(file.type) && !validExtensions.includes(ext)) {
      alert('Please upload a PDF, TXT, or MD file')
      return
    }
    
    setUploading(true)
    try {
      await onUpload(file)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragging(false)
      
      if (disabled || uploading) return
      
      const file = e.dataTransfer.files[0]
      if (file) handleFile(file)
    },
    [disabled, uploading]
  )

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
    e.target.value = ''
  }

  return (
    <Card
      className={cn(
        'transition-colors py-4',
        isDragging && 'border-crimson bg-crimson/5',
        disabled && 'opacity-50'
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <CardContent className="flex flex-col items-center gap-3 w-90">
        <div className={cn(
          'size-10 rounded-full flex items-center justify-center transition-colors',
          isDragging ? 'bg-crimson/10' : 'bg-accent'
        )}>
          {uploading ? (
            <Loader2 className="size-5 animate-spin text-muted-foreground" />
          ) : (
            <Upload className={cn(
              'size-5 transition-colors',
              isDragging ? 'text-crimson' : 'text-muted-foreground'
            )} />
          )}
        </div>
        <div className="text-center">
          <p className="text-sm font-medium">
            {uploading ? 'Uploading...' : 'Drop files here'}
          </p>
          <p className="text-xs text-muted-foreground">PDF, TXT, or MD</p>
        </div>
        <label>
          <input
            type="file"
            className="sr-only"
            accept=".pdf,.txt,.md,application/pdf,text/plain,text/markdown"
            onChange={handleInputChange}
            disabled={disabled || uploading}
          />
          <Button
            variant="outline"
            size="sm"
            disabled={disabled || uploading}
            asChild
          >
            <span className="cursor-pointer">
              <FileUp className="size-4" />
              Browse
            </span>
          </Button>
        </label>
      </CardContent>
    </Card>
  )
}
