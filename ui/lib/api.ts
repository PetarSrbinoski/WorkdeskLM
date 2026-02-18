import type {
  HealthResponse,
  DocumentsResponse,
  IngestResponse,
  ChatRequest,
  ChatResponse,
  CreateSessionRequest,
  CreateSessionResponse,
  GetSessionResponse,
  SummarizeSessionResponse,
  StudioBriefRequest,
  StudioBriefResponse,
  StudioFlashcardsRequest,
  StudioFlashcardsResponse,
} from './types'
import { apiBase } from './apiBase'

const API_BASE = apiBase()

class ApiError extends Error {
  status: number
  body?: string

  constructor(status: number, message: string, body?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

/**
 * Safe text read (never throws).
 */
async function safeReadText(res: Response): Promise<string> {
  try {
    return await res.text()
  } catch {
    return ''
  }
}

/**
 * Robust request helper:
 * - Catches network errors (fetch throws) and wraps them in ApiError(status=0)
 * - Handles non-2xx with readable body
 * - Handles empty responses
 * - Handles non-JSON responses cleanly
 */
async function request<T>(
  path: string,
  init?: RequestInit,
  opts?: { expectJson?: boolean }
): Promise<T> {
  const url = `${API_BASE}${path}`
  let response: Response

  try {
    response = await fetch(url, init)
  } catch (e) {
    // Network error: API down, DNS, CORS, mixed content, etc.
    throw new ApiError(0, `Network error calling ${path}: ${String(e)}`)
  }

  if (!response.ok) {
    const text = await safeReadText(response)
    const msg =
      text?.trim() ||
      `HTTP error ${response.status} ${response.statusText || ''}`.trim()
    throw new ApiError(response.status, msg, text)
  }

  // If caller doesn't want JSON, just return empty object or text if needed later.
  const expectJson = opts?.expectJson ?? true
  if (!expectJson) return undefined as unknown as T

  // Some endpoints might return empty body; avoid json() throwing.
  const text = await safeReadText(response)
  if (!text) return {} as T

  try {
    return JSON.parse(text) as T
  } catch {
    throw new ApiError(
      response.status,
      `Invalid JSON from ${path}`,
      text.slice(0, 2000)
    )
  }
}

// --------------------
// API calls
// --------------------

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export async function getDocuments(): Promise<DocumentsResponse> {
  return request<DocumentsResponse>('/documents')
}

export async function ingestDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append('file', file)

  return request<IngestResponse>('/ingest', {
    method: 'POST',
    body: formData,
  })
}

export async function deleteDocument(docId: string): Promise<void> {
  await request<void>(`/documents/${docId}`, { method: 'DELETE' }, { expectJson: false })
}

export async function chat(body: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

// Sessions
export async function createSession(
  body: CreateSessionRequest
): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>('/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  return request<GetSessionResponse>(`/sessions/${sessionId}`)
}

export async function summarizeSession(
  sessionId: string
): Promise<SummarizeSessionResponse> {
  return request<SummarizeSessionResponse>(`/sessions/${sessionId}/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
}

// Studio
export async function studioBrief(
  body: StudioBriefRequest
): Promise<StudioBriefResponse> {
  return request<StudioBriefResponse>('/studio/brief', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export async function studioFlashcards(
  body: StudioFlashcardsRequest
): Promise<StudioFlashcardsResponse> {
  return request<StudioFlashcardsResponse>('/studio/flashcards', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

export { ApiError }
