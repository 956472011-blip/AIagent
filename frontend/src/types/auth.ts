/**
 * 认证类型定义
 */

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