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
      setHealth(null)
      setError(err instanceof Error ? err.message : 'Failed to fetch health')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchHealth()
    // eslint-disable-next-line react-hooks/exhaustive-deps
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

  const qdrantOk = health?.services?.qdrant?.ok ?? false
  const llmOk = health?.services?.llm?.ok ?? false
  const allOk = qdrantOk && llmOk

  const llmLabel =
    health?.services?.llm?.expected?.provider === 'nvidia' ? 'NVIDIA' : 'LLM'

  return (
    <Card className={`py-4 ${!allOk ? 'border-amber-500/50' : ''} w-90`}>
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
              <Badge
                variant="secondary"
                className="gap-1 text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-0"
              >
                <CheckCircle2 className="size-3" />
                Online
              </Badge>
            ) : (
              <Badge
                variant="secondary"
                className="gap-1 text-xs bg-destructive/10 text-destructive border-0"
              >
                <XCircle className="size-3" />
                Offline
              </Badge>
            )}
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">{llmLabel}</span>
            {llmOk ? (
              <Badge
                variant="secondary"
                className="gap-1 text-xs bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-0"
              >
                <CheckCircle2 className="size-3" />
                Online
              </Badge>
            ) : (
              <Badge
                variant="secondary"
                className="gap-1 text-xs bg-destructive/10 text-destructive border-0"
              >
                <XCircle className="size-3" />
                Offline
              </Badge>
            )}
          </div>
        </div>

        {health?.embedding && (
          <div className="pt-2 border-t space-y-1">
            <p className="text-xs text-muted-foreground">
              Model:{' '}
              <span className="text-foreground">{health.embedding.model}</span>
            </p>
            <p className="text-xs text-muted-foreground">
              Dimensions:{' '}
              <span className="text-foreground">{health.embedding.dim}</span>
            </p>
          </div>
        )}

        {health?.services?.llm?.expected && (
          <div className="pt-2 border-t space-y-1">
            <p className="text-xs text-muted-foreground">
              Provider:{' '}
              <span className="text-foreground">
                {health.services.llm.expected.provider}
              </span>
            </p>
            <p className="text-xs text-muted-foreground">
              Fast:{' '}
              <span className="text-foreground">
                {health.services.llm.expected.fast_model}
              </span>
            </p>
            <p className="text-xs text-muted-foreground">
              Quality:{' '}
              <span className="text-foreground">
                {health.services.llm.expected.quality_model}
              </span>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
