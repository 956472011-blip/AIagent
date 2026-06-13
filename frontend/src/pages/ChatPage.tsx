/**
 * 聊天页面
 *
 * 企业级设计:
 *   - SSE 事件处理
 *   - 消息状态管理
 *   - 节点状态展示
 */

import { useState, useRef, useCallback } from 'react'
import { useAuth } from '@/contexts'
import { ChatMessage, ChatInput } from '@/components'
import type { ChatMessage as ChatMessageType, SSENodeEvent, SSEResultEvent } from '@/types'

// 节点名称映射
const NODE_NAMES: Record<string, string> = {
  classify_intent: '意图识别',
  reply_greeting: '生成回复',
  rewrite_query: '问题改写',
  retrieve: '检索文档',
  generate_answer: '生成答案',
  check_faithfulness: '质量检查',
  increment_retry: '重试',
}

// 生成唯一 ID
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

export function ChatPage() {
  const { user, logout } = useAuth()
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [streaming, setStreaming] = useState(false)
  const [currentNode, setCurrentNode] = useState<string>('')
  const esRef = useRef<EventSource | null>(null)

  // 发送消息
  const handleSend = useCallback((query: string) => {
    if (streaming) return

    // 添加用户消息
    const userMessage: ChatMessageType = {
      id: generateId(),
      role: 'user',
      content: query,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMessage])

    // 添加占位的助手消息
    const assistantMessage: ChatMessageType = {
      id: generateId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, assistantMessage])

    setStreaming(true)
    setCurrentNode('')

    // 建立 SSE 连接
    const url = `/api/chat/stream/get?q=${encodeURIComponent(query)}`
    const es = new EventSource(url)
    esRef.current = es

    // 处理节点事件
    es.addEventListener('node', (ev) => {
      try {
        const data: SSENodeEvent = JSON.parse(ev.data)
        setCurrentNode(data.node)
      } catch { /* ignore */ }
    })

    // 处理答案事件
    es.addEventListener('answer', (ev) => {
      const answer = ev.data
      setMessages((prev) => {
        const newMessages = [...prev]
        const lastMessage = newMessages[newMessages.length - 1]
        if (lastMessage?.role === 'assistant') {
          newMessages[newMessages.length - 1] = {
            ...lastMessage,
            content: lastMessage.content + answer,
          }
        }
        return newMessages
      })
    })

    // 处理结果事件
    es.addEventListener('result', (ev) => {
      try {
        const result: SSEResultEvent = JSON.parse(ev.data)
        setMessages((prev) => {
          const newMessages = [...prev]
          const lastMessage = newMessages[newMessages.length - 1]
          if (lastMessage?.role === 'assistant') {
            newMessages[newMessages.length - 1] = {
              ...lastMessage,
              content: result.answer,
              citations: result.citations,
              faithfulnessScore: result.faithfulness_score,
              reflection: result.reflection,
              retryCount: result.retry_count,
              intent: result.intent,
            }
          }
          return newMessages
        })
      } catch { /* ignore */ }
    })

    // 处理完成事件
    es.addEventListener('done', () => {
      es.close()
      esRef.current = null
      setStreaming(false)
      setCurrentNode('')
    })

    // 处理错误事件
    es.addEventListener('error', (ev) => {
      const errorMsg = ev.data || '未知错误'
      setMessages((prev) => {
        const newMessages = [...prev]
        const lastMessage = newMessages[newMessages.length - 1]
        if (lastMessage?.role === 'assistant') {
          newMessages[newMessages.length - 1] = {
            ...lastMessage,
            content: `(错误) ${errorMsg}`,
          }
        }
        return newMessages
      })
      es.close()
      esRef.current = null
      setStreaming(false)
      setCurrentNode('')
    })

    // 处理连接错误
    es.onerror = () => {
      es.close()
      esRef.current = null
      setStreaming(false)
      setCurrentNode('')
    }
  }, [streaming])

  return (
    <div className="mx-auto flex h-screen max-w-3xl flex-col p-4">
      {/* Header */}
      <header className="border-b pb-2 mb-4 flex justify-between items-center">
        <div>
          <h1 className="text-xl font-semibold">RAG Agent</h1>
          <p className="text-sm text-gray-500">欢迎, {user?.username}</p>
        </div>
        <button
          onClick={logout}
          className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
        >
          登出
        </button>
      </header>

      {/* Node Status */}
      {streaming && currentNode && (
        <div className="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
          <span className="inline-block animate-pulse mr-2">●</span>
          正在执行: {NODE_NAMES[currentNode] || currentNode}
        </div>
      )}

      {/* Messages */}
      <main className="flex-1 overflow-y-auto space-y-4">
        {messages.length === 0 && (
          <div className="text-gray-400 text-sm space-y-2">
            <p>我是企业知识库助手，可以回答关于 RAG、向量数据库、AI Agent 的问题。</p>
            <p className="text-xs">示例问题：</p>
            <ul className="text-xs space-y-1 ml-4 list-disc">
              <li>什么是 RAG？</li>
              <li>RAG 有哪些核心步骤？</li>
              <li>如何评估 RAG 系统的质量？</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage
            key={message.id}
            message={message}
            isStreaming={streaming && index === messages.length - 1 && message.role === 'assistant'}
          />
        ))}
      </main>

      {/* Input */}
      <ChatInput onSend={handleSend} disabled={streaming} />
    </div>
  )
}
