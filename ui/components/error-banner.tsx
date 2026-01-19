'use client'

import { Button } from '@/components/ui/button'
import { AlertCircle, X } from 'lucide-react'

interface ErrorBannerProps {
  message: string
  onDismiss: () => void
}

export function ErrorBanner({ message, onDismiss }: ErrorBannerProps) {
  return (
    <div className="fixed top-4 right-4 left-4 md:left-auto md:w-96 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
      <div className="bg-destructive text-white rounded-lg shadow-lg p-4 flex items-start gap-3">
        <AlertCircle className="size-5 shrink-0 mt-0.5" />
        <div className="flex-1 min-w-0">
          <p className="font-medium">Error</p>
          <p className="text-sm opacity-90 mt-1 break-words">{message}</p>
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          onClick={onDismiss}
          className="shrink-0 text-white hover:bg-white/20 hover:text-white"
        >
          <X className="size-4" />
        </Button>
      </div>
    </div>
  )
}
