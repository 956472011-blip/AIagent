# 代码迁移说明

## ✅ 已完成的迁移

### 1. `app/db/security.py` → `app/core/security.py`

**原因**: 密码加密属于核心功能,应放在 `core/` 目录

**影响文件**:
- `app/db/repositories/user_repo.py` - 已更新导入路径

**迁移后**:
```python
# 旧路径 ❌
from app.db.security import hash_password, verify_password

# 新路径 ✅
from app.core.security import hash_password, verify_password
```

---

## 🗑️ 已删除的旧代码

### 1. `app/api/auth/routes.py` (Session 认证)

**删除原因**:
- 使用 Session + Redis 认证
- 新版使用 JWT 认证,更符合企业级标准
- Session 认证需要 Redis,增加部署复杂度

**替代方案**:
- 使用 `app/services/auth_service.py` (JWT 认证)
- 使用 `app/middlewares/auth_middleware.py` (认证中间件)

### 2. `app/db/user_repo.py` (旧版用户仓储)

**删除原因**:
- 被 Session 认证使用
- 新版 `app/db/repositories/user_repo.py` 接口更清晰

**替代方案**:
- 使用 `app/db/repositories/user_repo.py`

### 3. `app/db/session.py` (Session 管理)

**删除原因**:
- Session 认证已删除
- JWT 认证不需要 Redis Session

**替代方案**:
- JWT Token 存储在前端(LocalStorage/Cookie)

### 4. Redis 配置 (从 config.py 移除)

**删除原因**:
- 不再使用 Session 认证
- 减少外部依赖

**清理的配置**:
```python
# 已删除 ❌
redis_url: str
redis_host: str
redis_port: int
session_expire_seconds: int
session_cookie_name: str
...
```

---

## 📊 最终目录结构(企业级)

```
app/
├── api/                       # API 层
│   ├── chat.py                # 聊天端点
│   ├── health.py              # 健康检查
│   └── ingest.py              # 文档入库
│
├── agents/                    # Agent 层
│   └── rag/                   # RAG Agent
│
├── services/                  # ✅ Service 层(业务逻辑)
│   ├── auth_service.py        # JWT 认证服务
│   └── chat_service.py        # 聊天服务
│
├── models/                    # ✅ Model 层(SQLModel)
│   ├── user.py                # 用户模型
│   └── chat_session.py        # 聊天会话模型
│
├── db/                        # 数据库层
│   ├── database.py            # 数据库连接池
│   └── repositories/          # ✅ Repository 层
│       └── user_repo.py       # 用户仓储
│
├── middlewares/               # ✅ Middleware 层
│   ├── auth_middleware.py     # JWT 认证中间件
│   └── logging_middleware.py  # 日志中间件
│
├── core/                      # 核心配置
│   ├── config.py              # 配置管理(JWT 配置)
│   ├── llm.py                 # LLM 客户端
│   └── security.py            # ✅ 密码加密(已迁移)
│
├── utils/                     # 工具类
├── constants/                 # 常量定义
└── tests/                     # 测试目录
```

---

## 🔐 认证方式对比

### 旧版(Session + Redis) ❌

```
用户登录
    ↓
创建 Session(存 Redis)
    ↓
返回 session_id(存 Cookie)
    ↓
每次请求携带 Cookie
    ↓
从 Redis 查询 Session
```

**缺点**:
- 需要 Redis,增加部署复杂度
- Session 存储在服务器,扩展性差
- Cookie 容易被 CSRF 攻击

### 新版(JWT) ✅

```
用户登录
    ↓
生成 JWT Token(包含用户信息)
    ↓
返回 Token(前端存储)
    ↓
每次请求携带 Token(Authorization Header)
    ↓
验证 Token 签名(无需存储)
```

**优点**:
- 无需 Redis,减少依赖
- Token 包含用户信息,服务器无状态
- 支持 CORS,适合前后端分离
- 更符合企业级标准

---

## 🚀 后续工作

- [x] 删除旧版认证代码
- [x] 更新 config.py(添加 JWT 配置)
- [x] 更新 main.py(移除 Redis 连接)
- [ ] 创建新的认证 API 端点
- [ ] 补充认证测试用例

---

## 📝 配置更新说明

### 需要在 .env 中添加:

```bash
# JWT 配置(生产环境必须修改 secret_key)
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### 已删除的配置:

```bash
# Redis 配置(已删除)
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379

# Session 配置(已删除)
SESSION_EXPIRE_SECONDS=86400
SESSION_COOKIE_NAME=session_id
...
```
