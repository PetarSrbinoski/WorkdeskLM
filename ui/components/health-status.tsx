'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { getHealth } from '@/lib/api'
import type { HealthResponse } from '@/lib/types'
import { CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getHealth()
      setHealth(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch health')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
  }, [])

  if (loading) {
    return (
      <Card className="py-4">
        <CardHeader className="py-0 pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive/50 py-4">
        <CardHeader className="py-0 pb-2">
          <CardTitle className="text-sm font-medium flex items-center justify-between">
            System Status
            <Button variant="ghost" size="icon-sm" onClick={fetchHealth}>
              <RefreshCw className="size-3" />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive text-xs">{error}</p>
        </CardContent>
      </Card>
    )
  }

  const qdrantOk = health?.services.qdrant.ok ?? false
  const ollamaOk = health?.services.ollama.ok ?? false
  const allOk = qdrantOk && ollamaOk

  return (
    <Card className={`py-4 ${!allOk ? 'border-amber-500/50' : ''}`}>
      <CardHeader className="py-0 pb-2">
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          System Status
          <Button variant="ghost" size="icon-sm" onClick={fetchHealth}>
            <RefreshCw className="size-3" />
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Qdrant</span>
            {qdrantOk ? (
              <Badge variant="secondary" className="gap-1 text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-0">
                <CheckCircle2 className="size-3" />
                Online
              </Badge>
            ) : (
              <Badge variant="secondary" className="gap-1 text-xs bg-destructive/10 text-destructive border-0">
                <XCircle className="size-3" />
                Offline
              </Badge>
            )}
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Ollama</span>
            {ollamaOk ? (
              <Badge variant="secondary" className="gap-1 text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-0">
                <CheckCircle2 className="size-3" />
                Online
              </Badge>
            ) : (
              <Badge variant="secondary" className="gap-1 text-xs bg-destructive/10 text-destructive border-0">
                <XCircle className="size-3" />
                Offline
              </Badge>
            )}
          </div>
        </div>
        {health?.embedding && (
          <div className="pt-2 border-t space-y-1">
            <p className="text-xs text-muted-foreground">
              Model: <span className="text-foreground">{health.embedding.model}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              Dimensions: <span className="text-foreground">{health.embedding.dim}</span>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
