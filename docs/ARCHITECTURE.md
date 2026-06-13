# 项目目录结构

## 📁 当前目录结构(简化版)

```
app/
├── __init__.py
├── main.py                    # FastAPI 应用入口
│
├── api/                       # API 层
│   ├── __init__.py
│   ├── auth/                  # 认证模块
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── chat.py                # 聊天端点
│   ├── health.py              # 健康检查
│   └── ingest.py              # 文档入库
│
├── agents/                    # Agent 层
│   ├── __init__.py
│   └── rag/                   # RAG Agent
│       ├── __init__.py
│       ├── graph.py           # StateGraph 组装
│       ├── nodes.py           # 节点函数
│       ├── prompts.py         # Prompt 模板
│       └── state.py           # 状态定义
│
├── services/                  # ✅ 服务层(业务逻辑)
│   ├── __init__.py
│   ├── chat_service.py        # 聊天服务
│   └── auth_service.py        # 认证服务
│
├── rag/                       # RAG 核心模块
│   ├── __init__.py
│   ├── embeddings.py          # 向量化
│   ├── hybrid_retriever.py    # Hybrid 检索
│   ├── loader.py              # 文档加载
│   ├── reranker.py            # Rerank 精排
│   ├── retriever.py           # 基础检索
│   ├── splitter.py            # 文本切片
│   └── vectorstore.py         # 向量存储
│
├── models/                    # ✅ 数据模型层
│   ├── __init__.py
│   ├── user.py                # 用户模型
│   └── chat_session.py        # 聊天会话模型
│
├── db/                        # 数据库层
│   ├── __init__.py
│   ├── database.py            # 数据库连接
│   ├── session.py             # Session 管理
│   ├── security.py            # 密码加密
│   ├── user_repo.py           # 旧版用户仓储
│   └── repositories/          # ✅ 仓储层
│       ├── __init__.py
│       └── user_repo.py       # 用户仓储
│
├── middlewares/               # ✅ 中间件层
│   ├── __init__.py
│   ├── auth_middleware.py     # JWT 认证中间件
│   └── logging_middleware.py  # 日志中间件
│
├── core/                      # 核心配置
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   └── llm.py                 # LLM 客户端
│
├── utils/                     # ✅ 工具类
│   ├── __init__.py
│   ├── llm_utils.py           # LLM 工具函数
│   └── text_utils.py          # 文本处理工具
│
├── constants/                 # ✅ 常量定义
│   ├── __init__.py
│   ├── intent_types.py        # 意图类型常量
│   └── error_codes.py         # 错误码定义
│
└── tests/                     # ✅ 测试目录
    ├── __init__.py
    ├── conftest.py            # pytest 配置
    └── test_agents/           # Agent 测试
        ├── __init__.py
        └── test_rag_graph.py
```

## 🎯 核心模块说明

### 1. API 层 (`api/`)
- **职责**: 参数校验、响应格式化、路由定义
- **原则**: 不包含业务逻辑,只调用 Service 层

### 2. Agent 层 (`agents/`)
- **职责**: LangGraph Agent 定义、节点函数、状态管理
- **原则**: 纯函数节点,无副作用,便于调试

### 3. Service 层 (`services/`)
- **职责**: 业务逻辑封装、事务管理、Agent 调用
- **原则**: 可被多个 API 复用,便于单元测试

### 4. RAG 层 (`rag/`)
- **职责**: 检索、向量化、文档处理
- **原则**: 可独立测试,与 Agent 解耦

### 5. Model 层 (`models/`)
- **职责**: 数据模型定义、ORM 映射
- **原则**: 使用 SQLModel 统一 Pydantic + SQLAlchemy

### 6. Repository 层 (`db/repositories/`)
- **职责**: 数据访问逻辑、SQL 查询
- **原则**: 与数据库解耦,便于切换数据源

### 7. Middleware 层 (`middlewares/`)
- **职责**: 认证、日志、错误处理
- **原则**: 横切关注点,统一处理

### 8. Utils 层 (`utils/`)
- **职责**: 通用工具函数
- **原则**: 无状态,纯函数

### 9. Constants 层 (`constants/`)
- **职责**: 常量定义、枚举类型
- **原则**: 避免魔法字符串,便于维护

### 10. Tests 层 (`tests/`)
- **职责**: 单元测试、集成测试
- **原则**: 测试覆盖核心逻辑,快速反馈

## 📝 待补充内容

- [ ] 补充 API 测试 (`test_api/`)
- [ ] 补充 RAG 测试 (`test_rag/`)
- [ ] 迁移旧代码到 Service 层
- [ ] 统一错误处理

## 🚀 后续优化

当项目规模扩大时,可以考虑:
1. API 版本控制 (`api/v1/`, `api/v2/`)
2. 更细粒度的测试分类
3. CI/CD 自动化测试
