/**
 * 认证 Context - JWT Token 管理
 *
 * 企业级设计:
 *   - Token 存储在 LocalStorage
 *   - 自动验证 Token 有效性
 *   - Token 过期自动跳转登录
 */

import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

import * as authApi from '@/api/auth'
import type { User } from '@/api/auth'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, email?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // 初始化:验证 Token
  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem('access_token')

      if (!token) {
        setLoading(false)
        return
      }

      try {
        // 验证 Token 有效性
        const userData = await authApi.getCurrentUser()
        setUser(userData)
      } catch (error) {
        // Token 无效,清除
        localStorage.removeItem('access_token')
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  // 登录
  const login = useCallback(async (username: string, password: string) => {
    const result = await authApi.login({ username, password })
    setUser(result.user)
  }, [])

  // 注册
  const register = useCallback(async (username: string, password: string, email?: string) => {
    const user = await authApi.register({ username, password, email })
    // 注册成功后自动登录
    await login(username, password)
    setUser(user)
  }, [login])

  // 登出
  const logout = useCallback(() => {
    authApi.logout()
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}