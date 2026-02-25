# 添加用户认证功能

## 概述

本change旨在为交易系统添加完整的用户认证功能，包括用户注册、登录、登出以及会话管理。使用Reflex框架实现前后端一体化的Python解决方案。

## 目标

- 实现用户注册功能，支持邮箱和密码注册
- 实现用户登录功能，支持邮箱/用户名和密码登录
- 实现会话管理（使用Reflex内置的认证机制）
- 实现密码加密存储（使用bcrypt）
- 实现登出功能
- 添加认证装饰器，保护需要认证的页面/功能
- 实现密码重置功能

## 非目标

- 本change不包含OAuth或第三方登录集成
- 不包含多因素认证（MFA）
- 不包含用户权限/角色管理（将在后续change中实现）

## 技术方案

### 后端实现（Python + Reflex）

1. **数据模型（DuckDB）**
   - 创建users表，包含：id、email、username、password_hash、created_at、updated_at字段
   - 使用Reflex内置的会话管理，无需创建sessions表

2. **Reflex状态管理**
   - 使用Reflex的State管理用户认证状态
   - 创建AuthState基类，包含用户信息和认证状态

3. **API端点（Reflex事件处理）**
   - 注册事件处理函数
   - 登录事件处理函数
   - 登出事件处理函数
   - 密码重置事件处理函数

4. **认证机制**
   - 使用Reflex内置的会话管理
   - 密码使用bcrypt加密，salt rounds: 10
   - 使用Python的secrets模块生成安全的token

5. **装饰器**
   - 创建require_auth装饰器，保护需要认证的页面

### 前端实现（Reflex组件）

1. **认证页面组件**
   - 注册页面组件
   - 登录页面组件
   - 密码重置页面组件

2. **导航组件**
   - 根据认证状态显示不同的导航选项

3. **状态绑定**
   - 使用Reflex的状态绑定机制实时更新UI

## 数据库变更（DuckDB）

```sql
-- 创建users表
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建password_reset_tokens表
CREATE TABLE password_reset_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
```

**注意**：UUID在Python代码中使用`uuid.uuid4()`生成，插入时作为字符串存储。

## 安全考虑

1. 密码必须使用bcrypt加密存储
2. 会话token使用secrets模块生成
3. 实现rate limiting防止暴力破解
4. HTTPS强制（生产环境）
5. 密码强度验证
6. 敏感信息不在日志中输出
7. 使用Reflex的CSRF保护机制

## 测试计划

1. 单元测试
   - 密码加密/验证函数
   - Token生成/验证函数
   - 认证装饰器

2. 集成测试
   - 注册流程
   - 登录流程
   - 登出流程
   - 密码重置流程

3. 安全测试
   - SQL注入测试
   - XSS测试
   - CSRF测试

## 依赖项（Python包）

- bcrypt: 密码加密
- reflex: 前后端框架
- pydantic: 数据验证
- email-validator: 邮箱验证

## 影响范围

- 新增Reflex页面组件
- 新增数据库表
- 新增认证相关的State和事件处理函数
- 现有页面需要添加认证保护

## 向后兼容性

本change为新增功能，不影响现有功能的兼容性。

## 实施步骤

1. 创建数据库初始化脚本
2. 实现用户数据模型
3. 实现认证State和事件处理函数
4. 创建认证装饰器
5. 实现前端认证页面组件
6. 添加路由保护
7. 编写测试
8. 更新文档

## 代码量估算

- 数据模型和数据库操作：~80行
- 认证State和事件处理：~100行
- 前端页面组件：~80行
- 装饰器和工具函数：~40行
- **总计：~300行**（符合单功能初始代码量≤300行的规范）
