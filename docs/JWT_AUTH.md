# JWT 认证实现详解

## 🔐 认证流程

### 1. 用户注册

```
POST /auth/register
{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com"
}

响应:
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com"
}
```

**流程**:
1. 校验用户名是否存在
2. bcrypt 加密密码
3. 创建用户记录
4. 返回用户信息

---

### 2. 用户登录

```
POST /auth/login
{
  "username": "testuser",
  "password": "password123"
}

响应:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser"
  }
}
```

**流程**:
1. 查询用户
2. 校验密码(bcrypt)
3. 生成 JWT Token
4. 返回 Token

---

### 3. 请求 API

```
GET /auth/me
Headers: Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

响应:
{
  "id": 1,
  "username": "testuser",
  "email": "test@example.com"
}
```

**流程**:
1. 中间件验证 Token 签名
2. 解析 Token payload
3. 查询用户信息
4. 返回用户信息

---

## 🛠️ 技术实现

### 1. JWT Token 结构

```javascript
// Token 组成
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0dXNlciIsInVzZXJfaWQiOjEsImV4cCI6MTcwMDAwMDAwMH0.signature

// 解码后
{
  "header": {
    "typ": "JWT",
    "alg": "HS256"
  },
  "payload": {
    "sub": "testuser",      // 用户名
    "user_id": 1,           // 用户 ID
    "exp": 1700000000       // 过期时间(时间戳)
  },
  "signature": "..."        // 签名
}
```

---

### 2. Token 生成

```python
# app/services/auth_service.py

def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
    """生成 JWT Token"""
    to_encode = data.copy()

    # 设置过期时间
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    # 编码 Token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,  # 密钥
        algorithm=settings.jwt_algorithm,  # HS256
    )

    return encoded_jwt
```

**关键参数**:
- `sub`: Subject(主题),通常是用户名
- `user_id`: 用户 ID
- `exp`: Expiration Time(过期时间)
- `iat`: Issued At(签发时间,可选)

---

### 3. Token 验证

```python
# app/middlewares/auth_middleware.py

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """验证 Token 并获取当前用户"""
    try:
        token = credentials.credentials

        # 解码 Token
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(401, "Token 无效")

    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token 已过期")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token 无效")

    # 查询用户
    user = await user_repo.get_by_username(username)
    if user is None:
        raise HTTPException(401, "用户不存在")

    return user
```

**验证步骤**:
1. 从 Authorization Header 提取 Token
2. 解码 Token(验证签名)
3. 检查过期时间
4. 查询用户信息
5. 返回用户信息

---

### 4. 密码加密

```python
# app/services/auth_service.py

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(self, password: str) -> str:
    """加密密码"""
    return pwd_context.hash(password)

def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    """校验密码"""
    return pwd_context.verify(plain_password, hashed_password)
```

**bcrypt 特点**:
- 单向加密,不可逆
- 自带盐值,防彩虹表攻击
- 计算成本可调,安全性高
- 企业级标准

---

## 🎯 API 端点

| 端点 | 方法 | 认证 | 说明 |
|------|------|------|------|
| `/auth/register` | POST | ❌ | 用户注册 |
| `/auth/login` | POST | ❌ | 用户登录 |
| `/auth/me` | GET | ✅ | 获取当前用户信息 |
| `/auth/refresh` | POST | ✅ | 刷新 Token |

---

## 🔒 安全设计

### 1. 密钥管理

```bash
# .env 文件
JWT_SECRET_KEY=your-super-secret-key-change-in-production
```

**生产环境要求**:
- 使用强随机密钥(至少 32 字符)
- 不要提交到 git
- 定期更换密钥

**生成强密钥**:
```bash
# 方法 1: openssl
openssl rand -hex 32

# 方法 2: Python
import secrets
print(secrets.token_hex(32))
```

---

### 2. Token 过期时间

```python
# config.py
jwt_expire_minutes: int = 30  # 默认 30 分钟
```

**建议**:
- 短期 Token: 15-30 分钟(高安全场景)
- 长期 Token: 7-30 天(用户体验优先)

---

### 3. HTTPS 强制

```python
# 生产环境强制 HTTPS
if settings.app_env == "prod":
    app.add_middleware(
        HTTPSRedirectMiddleware
    )
```

---

## 🧪 测试示例

### 1. 注册用户

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123",
    "email": "test@example.com"
  }'
```

### 2. 登录获取 Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }'
```

### 3. 使用 Token 访问 API

```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

---

## 🔄 Token 刷新策略

### 方案 1: 短期 Token + Refresh Token

```
登录
  ↓
返回 access_token(30分钟) + refresh_token(7天)
  ↓
access_token 过期
  ↓
用 refresh_token 刷新
  ↓
返回新的 access_token
```

### 方案 2: 自动刷新(简化版)

```
每次请求
  ↓
检查 Token 剩余有效期
  ↓
如果 < 5分钟,返回新 Token
```

---

## 📊 对比 Session 认证

| 特性 | JWT | Session |
|------|-----|---------|
| **存储位置** | 前端(LocalStorage/Cookie) | 服务器(Redis) |
| **服务器压力** | 低(无状态) | 高(需要存储) |
| **扩展性** | 易(无状态) | 难(需要共享 Session) |
| **跨域** | 支持 | 需要配置 |
| **安全性** | 中(依赖 HTTPS) | 高(可设置 HttpOnly) |
| **注销** | 难(Token 无法主动失效) | 易(直接删 Session) |

---

## 🚀 最佳实践

1. **短期 Token**: 设置较短的过期时间(15-30分钟)
2. **HTTPS 强制**: 生产环境必须使用 HTTPS
3. **密钥管理**: 使用环境变量,定期更换
4. **敏感操作**: 关键操作(如修改密码)要求重新验证
5. **Token 黑名单**: 注销时可维护黑名单(可选)

---

## 📝 前端集成

### React 示例

```typescript
// 登录
const login = async (username: string, password: string) => {
  const response = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })

  const { access_token } = await response.json()

  // 存储 Token
  localStorage.setItem('token', access_token)
}

// 请求 API
const fetchUser = async () => {
  const token = localStorage.getItem('token')

  const response = await fetch('/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  return response.json()
}
```
