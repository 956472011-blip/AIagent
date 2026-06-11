import { useRef, useState, type FormEvent } from 'react'

type Message = { role: 'user' | 'assistant'; content: string }

const THINK_RE = new RegExp('<think>[\s\S]*?</think>', 'g')

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  function send(e: FormEvent) {
    e.preventDefault()
    const q = input.trim()
    if (!q || streaming) return

    setMessages((m) => [...m, { role: 'user', content: q }])
    setInput('')
    setStreaming(true)

    // 先占位 assistant 消息,后续 chunk 累加 content
    setMessages((m) => [...m, { role: 'assistant', content: '' }])

    // EventSource 走 Vite proxy:/api -> http://127.0.0.1:8000
    const url = `/api/chat/stream/get?q=${encodeURIComponent(q)}`
    const es = new EventSource(url)
    esRef.current = es

    es.onmessage = (ev) => {
      const data = ev.data
      if (data === '[DONE]') {
        es.close()
        esRef.current = null
        setStreaming(false)
        return
      }
      if (data.startsWith('[ERROR]')) {
        es.close()
        esRef.current = null
        setStreaming(false)
        setMessages((m) => {
          const copy = [...m]
          copy[copy.length - 1] = { role: 'assistant', content: `(错误) ${data}` }
          return copy
        })
        return
      }
      // 过滤 <think>...</think> 块(M3 推理模型会带,前端不显示)
      const cleaned = data.replace(THINK_RE, '')
      if (!cleaned) return
      setMessages((m) => {
        const copy = [...m]
        copy[copy.length - 1] = {
          role: 'assistant',
          content: copy[copy.length - 1].content + cleaned,
        }
        return copy
      })
    }

    es.onerror = () => {
      es.close()
      esRef.current = null
      setStreaming(false)
    }
  }

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col p-4">
      <header className="border-b pb-2 mb-4">
        <h1 className="text-xl font-semibold">RAG Assistant</h1>
        <p className="text-sm text-gray-500">M1 流式对话 · M2 准备接 RAG</p>
      </header>

      <main className="flex-1 overflow-y-auto space-y-3">
        {messages.length === 0 && (
          <p className="text-gray-400 text-sm">问点什么吧,比如"用一句话介绍 RAG"。</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`rounded-lg px-3 py-2 text-sm whitespace-pre-wrap ${
              m.role === 'user'
                ? 'bg-blue-500 text-white ml-12'
                : 'bg-gray-100 text-gray-900 mr-12'
            }`}
          >
            {m.content || (streaming && i === messages.length - 1 ? '▍' : '')}
          </div>
        ))}
      </main>

      <form onSubmit={send} className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入问题,Enter 发送"
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          disabled={streaming}
        />
        <button
          type="submit"
          disabled={streaming}
          className="rounded-lg bg-blue-500 px-4 py-2 text-sm text-white disabled:opacity-50"
        >
          发送
        </button>
      </form>
    </div>
  )
}

export default App
