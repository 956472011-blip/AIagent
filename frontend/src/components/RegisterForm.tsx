/**
 * 注册表单组件
 */

import { useState } from 'react'
import { useAuth } from '@/contexts'
import { ApiError } from '@/api'

interface RegisterFormProps {
  onSuccess?: () => void
  onSwitchToLogin: () => void
}

export function RegisterForm({ onSuccess, onSwitchToLogin }: RegisterFormProps) {
  const { register } = useAuth()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await register({
        username,
        email,
        password,
        full_name: fullName || undefined,
      })
      onSuccess?.()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('注册失败，请重试')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          用户名
        </label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
          minLength={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="用户名（至少 3 位）"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          邮箱
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="your@email.com"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          密码
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="密码（至少 6 位）"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          姓名（可选）
        </label>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="您的姓名"
        />
      </div>

      {error && (
        <div className="p-3 bg-red-50 text-red-600 text-sm rounded-lg">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? '注册中...' : '注册'}
      </button>

      <p className="text-center text-sm text-gray-500">
        已有账号？{' '}
        <button
          type="button"
          onClick={onSwitchToLogin}
          className="text-blue-600 hover:underline"
        >
          立即登录
        </button>
      </p>
    </form>
  )
}
