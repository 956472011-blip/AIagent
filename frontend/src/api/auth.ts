/**
 * 认证 API
 *
 * 企业级 JWT 认证:
 *   - register: 用户注册
 *   - login: 用户登录,返回 Token
 *   - logout: 清除本地 Token
 *   - me: 获取当前用户信息
 *   - refresh: 刷新 Token
 */

import { get, post, setToken, clearToken } from './client'

export interface User {
  id: number
  username: string
  email?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  email?: string
}

export interface Token {
  access_token: string
  token_type: string
  user: User
}

/**
 * 用户注册
 */
export async function register(data: RegisterRequest): Promise<User> {
  return post<User>('/api/auth/register', data)
}

/**
 * 用户登录
 */
export async function login(data: LoginRequest): Promise<Token> {
  const result = await post<Token>('/api/auth/login', data)

  // 存储 Token
  setToken(result.access_token)

  return result
}

/**
 * 用户登出
 */
export function logout(): void {
  clearToken()
  window.location.href = '/login'
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<User> {
  return get<User>('/api/auth/me')
}

/**
 * 刷新 Token
 */
export async function refreshToken(): Promise<Token> {
  const result = await post<Token>('/api/auth/refresh', {})

  // 更新 Token
  setToken(result.access_token)

  return result
}