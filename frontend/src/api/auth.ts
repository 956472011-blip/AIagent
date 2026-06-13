/**
 * 认证 API
 */

import { api } from './client'
import type { User, LoginRequest, RegisterRequest, AuthStatus } from '@/types'

export const authApi = {
  /**
   * 用户登录
   */
  login: async (username: string, password: string): Promise<User> => {
    return api.post<User>('/auth/login', { username, password })
  },

  /**
   * 用户注册
   */
  register: async (data: RegisterRequest): Promise<User> => {
    return api.post<User>('/auth/register', data)
  },

  /**
   * 用户登出
   */
  logout: async (): Promise<void> => {
    return api.post('/auth/logout')
  },

  /**
   * 获取认证状态
   */
  getStatus: async (): Promise<AuthStatus> => {
    return api.get<AuthStatus>('/auth/status')
  },
}
