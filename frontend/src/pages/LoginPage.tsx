/**
 * 登录页面
 */

import { useState } from 'react'
import { LoginForm, RegisterForm } from '@/components'

interface LoginPageProps {
  onLoginSuccess: () => void
}

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [isLogin, setIsLogin] = useState(true)

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">RAG Agent</h1>
          <p className="text-gray-500 mt-2">企业知识库助手</p>
        </div>

        {/* Tab */}
        <div className="flex mb-6">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 text-center transition-colors ${
              isLogin
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 border-b border-gray-200 hover:text-gray-700'
            }`}
          >
            登录
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 text-center transition-colors ${
              !isLogin
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 border-b border-gray-200 hover:text-gray-700'
            }`}
          >
            注册
          </button>
        </div>

        {/* Form */}
        {isLogin ? (
          <LoginForm
            onSuccess={onLoginSuccess}
            onSwitchToRegister={() => setIsLogin(false)}
          />
        ) : (
          <RegisterForm
            onSuccess={onLoginSuccess}
            onSwitchToLogin={() => setIsLogin(true)}
          />
        )}
      </div>
    </div>
  )
}
