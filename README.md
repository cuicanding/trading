# AI Quant Trading

智能量化交易平台 - 基于Reflex框架的量化炒股分析Web应用

## 功能特性

- 用户认证（注册、登录、密码重置)
- 会话持久化
- 邮件通知(欢迎邮件、密码重置)

## 技术栈

- 前后端: Python + Reflex
- 数据库: DuckDB
- 邮件: SMTP

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
4. 在.env中配置:
   - SMTP_SERVER=smtp.qq.com
   - SMTP_PORT=465
   - SENDER_EMAIL=your_email@qq.com
   - SENDER_PASSWORD=授权码

### Gmail
1. 开启两步验证
2. 生成应用专用密码
3. 在.env中配置
   - SMTP_SERVER=smtp.gmail.com
   - SMTP_PORT=465
   - SENDER_EMAIL=your_email@gmail.com
   - SENDER_PASSWORD=应用专用密码

## 运行测试
```bash
pytest tests/ -v
```
