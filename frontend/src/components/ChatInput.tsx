/**
 * 聊天输入框组件
 */

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const form = e.currentTarget
    const input = form.elements.namedItem('message') as HTMLInputElement
    const message = input.value.trim()

    if (message && !disabled) {
      onSend(message)
      input.value = ''
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
      <input
        name="message"
        placeholder="输入问题，Enter 发送"
        className="flex-1 rounded-lg border border-gray-300 px-4 py-3 text-sm focus:border-blue-500 focus:outline-none disabled:bg-gray-100"
        disabled={disabled}
      />
      <button
        type="submit"
        disabled={disabled}
        className="rounded-lg bg-blue-500 px-6 py-3 text-sm text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-blue-600 transition-colors"
      >
        {disabled ? '处理中...' : '发送'}
      </button>
    </form>
  )
}
