/**
 * App 入口
 *
 * 企业级架构:
 *   - Provider 包装
 *   - 条件渲染
 *   - 清晰的路由逻辑
 */

import { useAuth, AuthProvider } from '@/contexts'
import { LoginPage, ChatPage } from '@/pages'

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth()

  // 加载状态
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  // 未登录 → 登录页
  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={() => {}} />
  }

  // 已登录 → 聊天页
  return <ChatPage />
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
