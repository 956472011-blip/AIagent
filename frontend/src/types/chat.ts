/**
 * 聊天相关类型定义
 */

export interface Citation {
  index: number
  source: string
  content_preview: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  faithfulnessScore?: number
  reflection?: string
  retryCount?: number
  intent?: string
  timestamp: number
}

export interface ChatSession {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface SSENodeEvent {
  node: string
  status: string
}

export interface SSEResultEvent {
  answer: string
  intent: string
  faithfulness_score: number
  citations: Citation[]
  reflection: string
  retry_count: number
}
