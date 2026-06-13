/**
 * 认证 Context
 *
 * 企业级设计:
 *   - 全局认证状态管理
 *   - 自动检查登录状态
 *   - 提供 login/logout 方法
 */

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react'
import { authApi } from '@/api'
import type { User, RegisterRequest, AuthContextType } from '@/types'

const AuthContext = createContext<AuthContextType | null>(null)

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const isAuthenticated = user !== null

  // 检查认证状态
  const checkAuth = useCallback(async () => {
    try {
      const status = await authApi.getStatus()
      setUser(status.is_authenticated ? status.user : null)
    } catch {
      setUser(null)
    }
  }, [])

  // 登录
  const login = useCallback(async (username: string, password: string) => {
    const loggedInUser = await authApi.login(username, password)
    setUser(loggedInUser)
  }, [])

  // 注册
  const register = useCallback(async (data: RegisterRequest) => {
    const newUser = await authApi.register(data)
    setUser(newUser)
  }, [])

  // 登出
  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
  }, [])

  // 初始化时检查认证状态
  useEffect(() => {
    checkAuth().finally(() => setIsLoading(false))
  }, [checkAuth])

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    register,
    logout,
    checkAuth,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

// 自定义 Hook
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}