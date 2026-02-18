// Health endpoint types
export interface HealthResponse {
  status: string
  services: {
    qdrant: { ok: boolean; error?: string }
    llm: { ok: boolean; error?: string }
  }
  embedding: {
    model: string
    dim: number
    collection: string
  }
}

// Document types
export interface Document {
  id: string
  name: string
  page_count: number
  chunk_count: number
  created_at: string
}

export interface DocumentsResponse {
  count: number
  documents: Document[]
}

export interface IngestResponse {
  doc_id: string
  name: string
  page_count: number
  chunk_count: number
  deduped: number
}

// Chat types
export type ChatMode = 'fast' | 'quality'

export interface ChatRequest {
  question: string
  mode: ChatMode
  top_k: number
  min_score: number
  doc_id?: string
  session_id?: string
}

export interface Citation {
  chunk_id: string
  score: number
  doc_name: string
  page_number: number
  chunk_index: number
  quote: string
}

export interface Latency {
  embed_ms: number
  qdrant_ms: number
  llm_ms: number
  total_ms: number
}

export interface ChatResponse {
  answer: string
  abstained: boolean
  mode_used: string
  model_used: string
  citations: Citation[]
  latency: Latency
}

// Studio types
export interface StudioBriefRequest {
  doc_id?: string
  question: string
  mode: 'quality'
}
export interface StudioBriefResponse {
  brief: string
}

export interface Flashcard {
  q: string
  a: string
}

export interface StudioFlashcardsRequest {
  doc_id?: string
  count: number
  mode: 'quality'
}
export interface StudioFlashcardsResponse {
  cards: Flashcard[]
}

// Sessions / workspaces
export interface CreateSessionRequest {
  title: string
}
export interface CreateSessionResponse {
  session_id: string
  title: string
}
export type SessionRole = 'user' | 'assistant' | 'system'
export interface SessionMessage {
  id: string
  role: SessionRole
  content: string
  created_at: string
}
export interface GetSessionResponse {
  session_id: string
  title: string
  created_at: string
  summary: string | null
  messages: SessionMessage[]
}
export interface SummarizeSessionResponse {
  session_id: string
  summary: string
}

// UI state types
export type ChatMessageKind = 'text' | 'flashcards'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  citations?: Citation[]
  latency?: Latency
  model_used?: string
  mode_used?: string
  abstained?: boolean

  // Gen 3 additions
  kind?: ChatMessageKind
  flashcards?: Flashcard[]
}
