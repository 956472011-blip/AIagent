/**
 * Axios HTTP Client 封装
 *
 * 企业级设计:
 *   - 统一错误处理
 *   - 请求/响应拦截器
 *   - 自动携带 Cookie
 *   - 类型安全
 */

import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios'

const API_BASE = '/api'

// 创建 axios 实例
export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  withCredentials: true, // 自动携带 Cookie
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 可以在这里添加 token 等认证信息
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    // 直接返回 data，调用方不用写 response.data
    return response.data
  },
  (error: AxiosError<{ detail?: string }>) => {
    // 统一错误处理
    const message = error.response?.data?.detail || error.message || '请求失败'
    const status = error.response?.status || 500

    // 401 未登录，可以跳转登录页
    if (status === 401) {
      // window.location.href = '/login'
    }

    return Promise.reject(new ApiError(status, message))
  }
)

/**
 * API 错误类
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

// 导出便捷方法
export const api = {
  get: <T>(url: string, params?: Record<string, string>) =>
    apiClient.get<T, T>(url, { params }),

  post: <T>(url: string, data?: unknown) =>
    apiClient.post<T, T>(url, data),

  put: <T>(url: string, data?: unknown) =>
    apiClient.put<T, T>(url, data),

  delete: <T>(url: string) =>
    apiClient.delete<T, T>(url),
}
