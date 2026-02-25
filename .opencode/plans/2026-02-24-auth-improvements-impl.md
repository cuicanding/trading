# 认证系统完善实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 完善认证系统：修复bug、会话持久化、邮件集成、测试文档

**Architecture:** 
1. 修复pages.py中所有事件处理函数的loading状态管理
2. 利用Reflex State持久化实现会话保持
3. 新增email_service.py模块处理邮件发送
4. 新增tests/目录编写单元测试和集成测试

**Tech Stack:** Python, Reflex, smtplib, pytest

---

## Task 1: Bug修复 - loading状态

**Files:**
- Modify: `pages.py:16-87` (RegisterState)
- Modify: `pages.py:93-136` (LoginState)
- Modify: `pages.py:154-186` (PasswordResetRequestState)
- Modify: `pages.py:222-271` (PasswordResetConfirmState)

### Step 1: 修复RegisterState.handle_register

将 `pages.py` 中 `handle_register` 方法改为 try-finally 模式：

```python
def handle_register(self):
    """处理注册请求"""
    self.clear_messages()
    self.is_loading = True
    try:
        # 验证邮箱或用户名
        if self.register_email:
            is_valid, error = self.validate_email(self.register_email)
            if not is_valid:
                self.error_message = error
                return

            user_repo = UserRepository()
            if user_repo.email_exists(self.register_email):
                self.error_message = "该邮箱已被注册"
                return

        elif self.register_username:
            is_valid, error = self.validate_username(self.register_username)
            if not is_valid:
                self.error_message = error
                return

            user_repo = UserRepository()
            if user_repo.username_exists(self.register_username):
                self.error_message = "该用户名已被注册"
                return

        else:
            self.error_message = "请输入邮箱或用户名"
            return

        is_valid, error = self.validate_password(self.register_password)
        if not is_valid:
            self.error_message = error
            return

        if self.register_password != self.register_password_confirm:
            self.error_message = "两次输入的密码不一致"
            return

        user_repo = UserRepository()
        user = user_repo.create_user(
            email=self.register_email if self.register_email else None,
            username=self.register_username if self.register_username else None,
            password=self.register_password
        )

        self.login(user)

        self.register_email = ""
        self.register_username = ""
        self.register_password = ""
        self.register_password_confirm = ""

        return rx.redirect("/")
    except Exception as e:
        self.error_message = f"注册失败: {str(e)}"
    finally:
        self.is_loading = False
```

### Step 2: 修复LoginState.handle_login

```python
def handle_login(self):
    """处理登录请求"""
    self.clear_messages()
    self.is_loading = True
    try:
        if not self.login_email_or_username:
            self.error_message = "请输入邮箱或用户名"
            return

        if not self.login_password:
            self.error_message = "请输入密码"
            return

        user_repo = UserRepository()
        user = None

        if '@' in self.login_email_or_username:
            user = user_repo.get_user_by_email(self.login_email_or_username)
        else:
            user = user_repo.get_user_by_username(self.login_email_or_username)

        if not user:
            self.error_message = "邮箱或密码错误"
            return

        if not user.verify_password(self.login_password):
            self.error_message = "邮箱或密码错误"
            return

        self.login(user)

        return rx.redirect("/")
    except Exception as e:
        self.error_message = f"登录失败: {str(e)}"
    finally:
        self.is_loading = False
```

### Step 3: 修复PasswordResetRequestState.handle_reset_request

```python
def handle_reset_request(self):
    """处理密码重置请求"""
    self.clear_messages()
    self.is_loading = True
    try:
        is_valid, error = self.validate_email(self.reset_email)
        if not is_valid:
            self.error_message = error
            return

        user_repo = UserRepository()
        user = user_repo.get_user_by_email(self.reset_email)

        if user:
            token = self.generate_secure_token()
            expires_at = self.get_token_expiry(hours=1)

            token_repo = PasswordResetTokenRepository()
            token_repo.create_token(user.id, token, expires_at)

            # TODO: 发送重置邮件
            print(f"密码重置链接: /reset-password?token={token}")

        self.success_message = "如果该邮箱已注册，重置链接将发送到您的邮箱"
        self.reset_email = ""
    except Exception as e:
        self.error_message = f"请求失败: {str(e)}"
    finally:
        self.is_loading = False
```

### Step 4: 修复PasswordResetConfirmState.handle_password_reset

```python
def handle_password_reset(self):
    """处理密码重置"""
    self.clear_messages()
    self.is_loading = True
    try:
        if not self.verify_token():
            return

        is_valid, error = self.validate_password(self.new_password)
        if not is_valid:
            self.error_message = error
            return

        if self.new_password != self.new_password_confirm:
            self.error_message = "两次输入的密码不一致"
            return

        token_repo = PasswordResetTokenRepository()
        token_record = token_repo.get_token(self.reset_token)

        user_repo = UserRepository()
        user = user_repo.get_user_by_id(token_record.user_id)

        if user:
            new_password_hash = User.hash_password(self.new_password)
            user_repo.conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [new_password_hash, user.id]
            )

            token_repo.mark_token_used(self.reset_token)

            self.success_message = "密码重置成功，请使用新密码登录"

            return rx.redirect("/login")
        else:
            self.error_message = "用户不存在"
    except Exception as e:
        self.error_message = f"重置失败: {str(e)}"
    finally:
        self.is_loading = False
```

### Step 5: 验证修复

Run: `python -c "from pages import *; print('Import OK')"`
Expected: 无错误

---

## Task 2: 会话持久化

**Files:**
- Modify: `auth.py:12-61` (AuthState)
- Modify: `trading_app/trading_app.py:85-244` (index page)

### Step 1: 修复AuthState的is_authenticated属性冲突

修改 `auth.py`，移除属性和变量冲突：

```python
class AuthState(rx.State):
    """认证状态基类"""
    
    current_user_id: Optional[str] = None
    current_user_email: Optional[str] = None
    current_user_username: Optional[str] = None
    
    register_email: str = ""
    register_username: str = ""
    register_password: str = ""
    register_password_confirm: str = ""
    
    login_email_or_username: str = ""
    login_password: str = ""
    
    error_message: str = ""
    success_message: str = ""
    
    is_loading: bool = False
    
    @rx.var
    def is_authenticated(self) -> bool:
        """检查用户是否已认证"""
        return self.current_user_id is not None
    
    @rx.var
    def current_user(self) -> Optional[dict]:
        """获取当前用户信息"""
        if self.current_user_id:
            return {
                "id": self.current_user_id,
                "email": self.current_user_email,
                "username": self.current_user_username
            }
        return None
    
    def login(self, user: User):
        """登录用户"""
        self.current_user_id = user.id
        self.current_user_email = user.email
        self.current_user_username = user.username
        self.success_message = "登录成功"
        self.error_message = ""
    
    def logout(self):
        """登出用户"""
        self.current_user_id = None
        self.current_user_email = None
        self.current_user_username = None
        self.success_message = "登出成功"
        self.error_message = ""
    
    def clear_messages(self):
        """清除消息"""
        self.error_message = ""
        self.success_message = ""
```

### Step 2: 验证会话持久化

Run: `python -c "from auth import AuthState; print('AuthState OK')"`
Expected: 无错误

---

## Task 3: 邮件服务模块

**Files:**
- Create: `email_service.py`
- Create: `config.py`
- Modify: `requirements.txt`

### Step 1: 创建配置文件

创建 `config.py`:

```python
import os

class Config:
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "465"))
    SENDER_EMAIL: str = os.getenv("SENDER_EMAIL", "")
    SENDER_PASSWORD: str = os.getenv("SENDER_PASSWORD", "")
    APP_NAME: str = "AI Quant Trading"
    APP_URL: str = os.getenv("APP_URL", "http://localhost:3000")
```

### Step 2: 创建邮件服务模块

创建 `email_service.py`:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from config import Config


class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.sender_email = Config.SENDER_EMAIL
        self.sender_password = Config.SENDER_PASSWORD
    
    def is_configured(self) -> bool:
        """检查邮件服务是否已配置"""
        return bool(self.sender_email and self.sender_password)
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """发送邮件"""
        if not self.is_configured():
            print(f"[邮件未配置] 收件人: {to_email}, 主题: {subject}")
            return False
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{Config.APP_NAME} <{self.sender_email}>"
            msg["To"] = to_email
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            if html_body:
                msg.attach(MIMEText(html_body, "html", "utf-8"))
            
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            return True
        except Exception as e:
            print(f"发送邮件失败: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """发送欢迎邮件"""
        subject = f"欢迎加入 {Config.APP_NAME}"
        body = f"""
您好 {username}，

欢迎加入 {Config.APP_NAME}！

您现在可以使用我们的量化交易平台进行股票分析和策略回测。

如有任何问题，请随时联系我们。

祝您投资顺利！
{Config.APP_NAME} 团队
"""
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #00f0ff;">欢迎加入 {Config.APP_NAME}</h2>
    <p>您好 <strong>{username}</strong>，</p>
    <p>欢迎加入 {Config.APP_NAME}！</p>
    <p>您现在可以使用我们的量化交易平台进行股票分析和策略回测。</p>
    <p>如有任何问题，请随时联系我们。</p>
    <p>祝您投资顺利！</p>
    <p style="color: #888;">{Config.APP_NAME} 团队</p>
</body>
</html>
"""
        return self.send_email(to_email, subject, body, html_body)
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """发送密码重置邮件"""
        reset_link = f"{Config.APP_URL}/reset-password?token={reset_token}"
        subject = f"重置您的密码 - {Config.APP_NAME}"
        body = f"""
您好，

您收到这封邮件是因为您请求重置密码。

请点击以下链接重置密码（链接1小时内有效）：
{reset_link}

如果您没有请求重置密码，请忽略此邮件。

{Config.APP_NAME} 团队
"""
        html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2 style="color: #00f0ff;">重置您的密码</h2>
    <p>您好，</p>
    <p>您收到这封邮件是因为您请求重置密码。</p>
    <p>
        <a href="{reset_link}" style="background: linear-gradient(135deg, #00f0ff, #7000ff); color: #0a0a0f; padding: 14px 24px; text-decoration: none; border-radius: 8px; font-weight: 600;">
            点击重置密码
        </a>
    </p>
    <p style="color: #888;">链接1小时内有效</p>
    <p style="color: #888; font-size: 12px;">如果您没有请求重置密码，请忽略此邮件。</p>
    <hr style="border: 1px solid #333;">
    <p style="color: #888;">{Config.APP_NAME} 团队</p>
</body>
</html>
"""
        return self.send_email(to_email, subject, body, html_body)


email_service = EmailService()
```

### Step 3: 更新requirements.txt

```
reflex
bcrypt
email-validator
duckdb
python-dotenv
```

### Step 4: 集成邮件服务到注册流程

修改 `pages.py` 中 `RegisterState.handle_register`，在创建用户后添加：

```python
from email_service import email_service

# 在 user = user_repo.create_user(...) 之后添加：
email_service.send_welcome_email(user.email, user.username or user.email)
```

### Step 5: 集成邮件服务到密码重置流程

修改 `pages.py` 中 `PasswordResetRequestState.handle_reset_request`：

```python
from email_service import email_service

# 替换 print(f"密码重置链接: ...") 为：
email_service.send_password_reset_email(user.email, token)
```

---

## Task 4: 环境变量配置

**Files:**
- Create: `.env.example`
- Modify: `.gitignore`

### Step 1: 创建.env.example

```env
SMTP_SERVER=smtp.qq.com
SMTP_PORT=465
SENDER_EMAIL=your_email@qq.com
SENDER_PASSWORD=your_authorization_code
APP_URL=http://localhost:3000
```

### Step 2: 更新.gitignore

添加：
```
.env
__pycache__/
*.pyc
.trading.db
```

---

## Task 5: 修复现有LSP类型错误

**Files:**
- Modify: `models.py`
- Modify: `pages.py`

### Step 1: 修复models.py的类型注解

在 `UserRepository` 类中修改 `connect` 方法的返回类型和类型检查：

```python
def connect(self):
    """连接到数据库"""
    if self.conn is None:
        self.conn = duckdb.connect(self.db_path)
    return self.conn

def _ensure_conn(self):
    """确保连接存在"""
    if self.conn is None:
        self.connect()
    return self.conn
```

然后在使用 `self.conn` 之前调用 `self._ensure_conn()`。

### Step 2: 修复pages.py的类型问题

修改 `tech_heading` 和 `tech_text` 函数的 size 参数：

```python
def tech_heading(text: str, size: str = "7") -> rx.Component:
    return rx.heading(
        text,
        size=size,  # Reflex会自动处理
        ...
    )
```

---

## Task 6: 测试

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_models.py`
- Create: `tests/test_auth.py`
- Create: `tests/test_email.py`

### Step 1: 创建测试目录

```bash
mkdir tests
```

### Step 2: 创建tests/__init__.py

```python
```

### Step 3: 创建tests/test_models.py

```python
import pytest
from datetime import datetime, timedelta
from models import User, PasswordResetToken


class TestUser:
    def test_hash_password(self):
        password = "testpassword123"
        hashed = User.hash_password(password)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        password = "testpassword123"
        user = User(id="test-id", password_hash=User.hash_password(password))
        assert user.verify_password(password) is True
    
    def test_verify_password_incorrect(self):
        password = "testpassword123"
        user = User(id="test-id", password_hash=User.hash_password(password))
        assert user.verify_password("wrongpassword") is False
    
    def test_to_dict(self):
        user = User(id="test-id", email="test@test.com", username="testuser")
        d = user.to_dict()
        assert d["id"] == "test-id"
        assert d["email"] == "test@test.com"
        assert d["username"] == "testuser"


class TestPasswordResetToken:
    def test_is_expired_false(self):
        token = PasswordResetToken(
            id="test-id",
            user_id="user-id",
            token="test-token",
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert token.is_expired() is False
    
    def test_is_expired_true(self):
        token = PasswordResetToken(
            id="test-id",
            user_id="user-id",
            token="test-token",
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert token.is_expired() is True
```

### Step 4: 创建tests/test_auth.py

```python
import pytest
from auth import AuthState


class TestAuthState:
    def test_validate_email_valid(self):
        state = AuthState()
        is_valid, error = state.validate_email("test@test.com")
        assert is_valid is True
        assert error == ""
    
    def test_validate_email_empty(self):
        state = AuthState()
        is_valid, error = state.validate_email("")
        assert is_valid is False
        assert "空" in error
    
    def test_validate_email_invalid_format(self):
        state = AuthState()
        is_valid, error = state.validate_email("invalid-email")
        assert is_valid is False
        assert "格式" in error
    
    def test_validate_username_valid(self):
        state = AuthState()
        is_valid, error = state.validate_username("testuser")
        assert is_valid is True
        assert error == ""
    
    def test_validate_username_too_short(self):
        state = AuthState()
        is_valid, error = state.validate_username("ab")
        assert is_valid is False
        assert "3-20" in error
    
    def test_validate_password_valid(self):
        state = AuthState()
        is_valid, error = state.validate_password("password123")
        assert is_valid is True
        assert error == ""
    
    def test_validate_password_too_short(self):
        state = AuthState()
        is_valid, error = state.validate_password("pass12")
        assert is_valid is False
        assert "8" in error
    
    def test_validate_password_no_digit(self):
        state = AuthState()
        is_valid, error = state.validate_password("password")
        assert is_valid is False
        assert "数字" in error
```

### Step 5: 创建tests/test_email.py

```python
import pytest
from unittest.mock import patch, MagicMock
from email_service import EmailService


class TestEmailService:
    def test_is_configured_false(self):
        service = EmailService()
        service.sender_email = ""
        service.sender_password = ""
        assert service.is_configured() is False
    
    def test_is_configured_true(self):
        service = EmailService()
        service.sender_email = "test@test.com"
        service.sender_password = "password"
        assert service.is_configured() is True
    
    @patch("email_service.smtplib.SMTP_SSL")
    def test_send_email_success(self, mock_smtp):
        service = EmailService()
        service.sender_email = "test@test.com"
        service.sender_password = "password"
        
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        result = service.send_email(
            to_email="recipient@test.com",
            subject="Test Subject",
            body="Test Body"
        )
        
        assert result is True
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()
```

### Step 6: 运行测试

```bash
pip install pytest
pytest tests/ -v
```

---

## Task 7: 文档更新

**Files:**
- Create: `README.md`
- Create: `docs/deployment.md`

### Step 1: 创建README.md

```markdown
# AI Quant Trading

智能量化交易平台 - 基于Reflex框架的量化炒股分析Web应用

## 功能特性

- 用户认证（注册、登录、密码重置）
- 会话持久化
- 邮件通知（欢迎邮件、密码重置）

## 技术栈

- 前后端：Python + Reflex
- 数据库：DuckDB
- 邮件：SMTP

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
python db_init.py
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入SMTP配置
```

### 4. 启动应用

```bash
cd trading_app
reflex run
```

## SMTP配置

### QQ邮箱

1. 登录QQ邮箱 → 设置 → 账户
2. 开启POP3/SMTP服务
3. 生成授权码
4. 在.env中配置：
   - SMTP_SERVER=smtp.qq.com
   - SMTP_PORT=465
   - SENDER_EMAIL=your_email@qq.com
   - SENDER_PASSWORD=授权码

### Gmail

1. 开启两步验证
2. 生成应用专用密码
3. 在.env中配置：
   - SMTP_SERVER=smtp.gmail.com
   - SMTP_PORT=465
   - SENDER_EMAIL=your_email@gmail.com
   - SENDER_PASSWORD=应用专用密码

## 运行测试

```bash
pytest tests/ -v
```

## 许可证

MIT
```

### Step 2: 创建docs/deployment.md

```markdown
# 部署指南

## 生产环境部署

### 1. 环境准备

- Python 3.10+
- HTTPS证书

### 2. 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
nano .env
```

### 3. 安全配置

- 使用HTTPS
- 不要在代码中硬编码凭证
- 定期更新依赖

### 4. 启动

```bash
reflex run --env prod
```
```

---

## 执行顺序

1. Task 1: Bug修复 (最高优先级)
2. Task 2: 会话持久化
3. Task 5: 修复LSP类型错误
4. Task 3: 邮件服务模块
5. Task 4: 环境变量配置
6. Task 6: 测试
7. Task 7: 文档更新
