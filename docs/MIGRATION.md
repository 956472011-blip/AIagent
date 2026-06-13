# 代码迁移说明

## ✅ 已完成的迁移

### 1. `app/db/security.py` → `app/core/security.py`

**原因**: 密码加密属于核心功能,应放在 `core/` 目录

**影响文件**:
- `app/db/repositories/user_repo.py` - 已更新导入路径
- `app/db/user_repo.py` - 已更新导入路径

**迁移后**:
```python
# 旧路径 ❌
from app.db.security import hash_password, verify_password

# 新路径 ✅
from app.core.security import hash_password, verify_password
```

---

## ⚠️ 暂时保留的旧代码

### 1. `app/db/user_repo.py` (旧版用户仓储)

**保留原因**:
- 新版 `app/db/repositories/user_repo.py` 接口不同
- 旧版被 `app/api/auth/routes.py` 使用(Session 认证)
- 新版用于 JWT 认证

**后续计划**:
- 统一认证方式(Session 或 JWT)
- 迁移到新版仓储接口

### 2. `app/api/auth/routes.py` (Session 认证)

**保留原因**:
- 使用 Session + Redis 认证
- 新版 `app/services/auth_service.py` 使用 JWT 认证
- 两套认证方式并存

**后续计划**:
- 统一使用 JWT 认证
- 迁移 Session 认证逻辑到 Service 层

---

## 📊 当前目录结构(优化后)

```
app/
├── core/                     # 核心配置
│   ├── config.py             # 配置管理
│   ├── llm.py                # LLM 客户端
│   └── security.py           # ✅ 密码加密(已迁移)
│
├── db/                       # 数据库层
│   ├── database.py           # 数据库连接
│   ├── session.py            # Session 管理(Redis)
│   ├── user_repo.py          # ⚠️ 旧版用户仓储(暂时保留)
│   └── repositories/         # ✅ 新版仓储层
│       └── user_repo.py      # 新版用户仓储
│
├── api/auth/                 # ⚠️ 旧版认证(Session)
│   └── routes.py
│
├── services/                 # ✅ 新版 Service 层
│   ├── auth_service.py       # 新版认证服务(JWT)
│   └── chat_service.py
```

---

## 🚀 后续优化建议

### P0(立即执行)
- [x] 迁移 `security.py` 到 `core/`
- [x] 更新所有导入路径

### P1(后续优化)
- [ ] 统一认证方式(Session 或 JWT)
- [ ] 迁移旧版 `user_repo.py` 到新版接口
- [ ] 补充测试用例

### P2(可选)
- [ ] 删除旧版代码(确认不再使用后)
- [ ] API 版本控制(`api/v1/`)

---

## 💡 迁移原则

1. **渐进式迁移**: 不破坏现有功能,逐步迁移
2. **保留旧版本**: 新旧版本并存,确认稳定后再删除旧代码
3. **更新文档**: 每次迁移后更新此文档

---

## 📝 迁移检查清单

- [x] 检查文件是否被引用
- [x] 更新所有导入路径
- [x] 运行测试验证功能
- [x] 更新文档说明
