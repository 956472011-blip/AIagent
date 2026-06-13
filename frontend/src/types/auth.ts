/**
 * 认证相关类型定义
 */

export interface User {
  id: number
  username: string
  email: string
  full_name: string | null
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface AuthStatus {
  is_authenticated: boolean
  user: User | null
}

export interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  register: (data: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}
