'use client'

import { useCallback, useEffect, useState } from 'react'
import { createSession, getSession } from '@/lib/api'
import type { GetSessionResponse } from '@/lib/types'
import { ApiError } from '@/lib/api'

const STORAGE_KEY = 'workdesklm_session_id'

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [session, setSession] = useState<GetSessionResponse | null>(null)
  const [initializing, setInitializing] = useState(true)

  const persist = useCallback((id: string) => {
    try {
      localStorage.setItem(STORAGE_KEY, id)
    } catch {
      // ignore
    }
  }, [])

  const loadSession = useCallback(
    async (id: string) => {
      const data = await getSession(id)
      setSessionId(data.session_id)
      setSession(data)
      persist(data.session_id)
      return data
    },
    [persist]
  )

  const createNewSession = useCallback(async () => {
    const created = await createSession({ title: 'New session' })
    setSessionId(created.session_id)
    persist(created.session_id)

    try {
      const data = await getSession(created.session_id)
      setSession(data)
      return data
    } catch {
      const shell: GetSessionResponse = {
        session_id: created.session_id,
        title: created.title,
        created_at: new Date().toISOString(),
        summary: null,
        messages: [],
      }
      setSession(shell)
      return shell
    }
  }, [persist])

  useEffect(() => {
    let cancelled = false

    async function init() {
      setInitializing(true)
      try {
        const existing = (() => {
          try {
            return localStorage.getItem(STORAGE_KEY)
          } catch {
            return null
          }
        })()

        if (existing) {
          try {
            await loadSession(existing)
          } catch (e) {
            if (e instanceof ApiError && e.status === 404) {
              await createNewSession()
            } else {
              await createNewSession()
            }
          }
        } else {
          await createNewSession()
        }
      } finally {
        if (!cancelled) setInitializing(false)
      }
    }

    init()
    return () => {
      cancelled = true
    }
  }, [createNewSession, loadSession])

  return {
    sessionId,
    session,
    setSession,
    initializing,
    createNewSession,
    loadSession,
  }
}
