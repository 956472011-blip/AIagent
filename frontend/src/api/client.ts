/**
 * API Client - JWT 认证
 *
 * 企业级设计:
 *   - 自动携带 JWT Token
 *   - Token 过期自动跳转登录
 *   - 统一错误处理
 *   - 使用 URL API 处理查询参数(避免手动拼接错误)
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

/**
 * 获取存储的 Token
 */
function getToken(): string | null {
  return localStorage.getItem('access_token')
}

/**
 * 存储 Token
 */
export function setToken(token: string): void {
  localStorage.setItem('access_token', token)
}

/**
 * 清除 Token
 */
export function clearToken(): void {
  localStorage.removeItem('access_token')
}

/**
 * 通用请求函数
 */
async function request<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  const token = getToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options?.headers,
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  })

  // 处理错误
  if (!response.ok) {
    if (response.status === 401) {
      // Token 过期或无效,清除并跳转登录
      clearToken()
      window.location.href = '/login'
      throw new Error('认证失败,请重新登录')
    }

    const error = await response.json().catch(() => ({ detail: '请求失败' }))
    throw new Error(error.detail || '请求失败')
  }

  return response.json()
}

/**
 * GET 请求
 */
export async function get<T>(url: string): Promise<T> {
  return request<T>(url, { method: 'GET' })
}

/**
 * POST 请求
 */
export async function post<T>(url: string, data?: unknown): Promise<T> {
  return request<T>(url, {
    method: 'POST',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * PUT 请求
 */
export async function put<T>(url: string, data?: unknown): Promise<T> {
  return request<T>(url, {
    method: 'PUT',
    body: data ? JSON.stringify(data) : undefined,
  })
}

/**
 * DELETE 请求
 */
export async function del<T>(url: string): Promise<T> {
  return request<T>(url, { method: 'DELETE' })
}

/**
 * SSE 流式请求
 *
 * 使用 URL API 处理查询参数,自动管理 ? 和 &
 * 避免手动拼接 URL 错误
 *
 * 示例:
 *   输入: "/api/chat/stream/get?q=你好"
 *   输出: "http://localhost:8000/api/chat/stream/get?q=你好&token=xxx"
 */
export function createEventSource(url: string): EventSource {
  const token = getToken()

  // 拼接基础地址(处理绝对路径和相对路径)
  const urlObj = new URL(url, API_BASE_URL || window.location.origin)

  // 追加 token 参数(URL API 自动管理 ? 和 &)
  if (token) {
    urlObj.searchParams.set('token', token)
  }

  return new EventSource(urlObj.href)
}