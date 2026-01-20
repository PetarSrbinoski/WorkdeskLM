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
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text()
    throw new ApiError(response.status, text || `HTTP error ${response.status}`)
  }
  return response.json()
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`)
  return handleResponse<HealthResponse>(response)
}

export async function getDocuments(): Promise<DocumentsResponse> {
  const response = await fetch(`${API_BASE}/documents`)
  return handleResponse<DocumentsResponse>(response)
}

export async function ingestDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/ingest`, {
    method: 'POST',
    body: formData,
  })
  return handleResponse<IngestResponse>(response)
}

export async function deleteDocument(docId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const text = await response.text()
    throw new ApiError(response.status, text || `HTTP error ${response.status}`)
  }
}

export async function chat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  return handleResponse<ChatResponse>(response)
}

// Sessions
export async function createSession(
  body: CreateSessionRequest
): Promise<CreateSessionResponse> {
  const response = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return handleResponse<CreateSessionResponse>(response)
}

export async function getSession(sessionId: string): Promise<GetSessionResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}`)
  return handleResponse<GetSessionResponse>(response)
}

export async function summarizeSession(
  sessionId: string
): Promise<SummarizeSessionResponse> {
  const response = await fetch(`${API_BASE}/sessions/${sessionId}/summarize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
  })
  return handleResponse<SummarizeSessionResponse>(response)
}

// Studio
export async function studioBrief(
  body: StudioBriefRequest
): Promise<StudioBriefResponse> {
  const response = await fetch(`${API_BASE}/studio/brief`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return handleResponse<StudioBriefResponse>(response)
}

export async function studioFlashcards(
  body: StudioFlashcardsRequest
): Promise<StudioFlashcardsResponse> {
  const response = await fetch(`${API_BASE}/studio/flashcards`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  return handleResponse<StudioFlashcardsResponse>(response)
}

export { ApiError }
