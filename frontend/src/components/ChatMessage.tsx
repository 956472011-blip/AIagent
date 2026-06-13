/**
 * 聊天消息组件
 */

import type { ChatMessage as ChatMessageType } from '@/types'

interface ChatMessageProps {
  message: ChatMessageType
  isStreaming?: boolean
}

export function ChatMessage({ message, isStreaming }: ChatMessageProps) {
  const { role, content, citations, faithfulnessScore, retryCount } = message

  // 渲染带引用标注的答案
  const renderContentWithCitations = () => {
    if (!citations || citations.length === 0) {
      return <span className="whitespace-pre-wrap">{content}</span>
    }

    const parts = content.split(/(\[\d+\])/g)
    return (
      <span className="whitespace-pre-wrap">
        {parts.map((part, i) => {
          const match = part.match(/\[(\d+)\]/)
          if (match) {
            const idx = parseInt(match[1], 10)
            const citation = citations.find((c) => c.index === idx)
            return (
              <span
                key={i}
                className="inline-flex items-center justify-center w-5 h-5 text-xs bg-blue-100 text-blue-700 rounded-full cursor-pointer hover:bg-blue-200 mx-0.5"
                title={citation?.content_preview || `来源 ${idx}`}
              >
                {idx}
              </span>
            )
          }
          return part
        })}
      </span>
    )
  }

  return (
    <div
      className={`rounded-lg px-4 py-3 ${
        role === 'user'
          ? 'bg-blue-500 text-white ml-16'
          : 'bg-gray-50 text-gray-900 mr-16'
      }`}
    >
      {/* 消息内容 */}
      <div className="text-sm leading-relaxed">
        {role === 'assistant' ? (
          content || (isStreaming ? (
            <span className="text-gray-400">思考中...</span>
          ) : null)
        ) : (
          content
        )}
        {role === 'assistant' && content && renderContentWithCitations()}
      </div>

      {/* 引用来源 */}
      {role === 'assistant' && citations && citations.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500 mb-2">参考来源：</p>
          <div className="space-y-1">
            {citations.map((c) => (
              <div key={c.index} className="text-xs text-gray-600 flex items-start gap-2">
                <span className="inline-flex items-center justify-center w-4 h-4 text-[10px] bg-gray-200 rounded flex-shrink-0 mt-0.5">
                  {c.index}
                </span>
                <span className="truncate">{c.source}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 自检结果 */}
      {role === 'assistant' && faithfulnessScore !== undefined && (
        <div className="mt-2 pt-2 border-t border-gray-200 flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span
              className={`inline-block w-2 h-2 rounded-full ${
                faithfulnessScore >= 0.7 ? 'bg-green-500' : 'bg-yellow-500'
              }`}
            />
            忠实度: {(faithfulnessScore * 100).toFixed(0)}%
          </span>
          {retryCount && retryCount > 0 && (
            <span>重试次数: {retryCount}</span>
          )}
        </div>
      )}
    </div>
  )
}
