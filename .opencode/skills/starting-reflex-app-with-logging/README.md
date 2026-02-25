# Starting Reflex App with Logging

这个技能提供了自动启动Reflex应用并记录日志的工具，帮助快速诊断启动问题和运行时错误。

## 文件说明

- `start_reflex.bat` - Windows启动脚本
- `start_reflex.py` - 跨平台启动脚本（推荐）
- `check_log.py` - 日志查看工具
- `.opencode/skills/starting-reflex-app-with-logging/SKILL.md` - 技能文档

## 快速开始

### 1. 启动应用（Windows）
```cmd
start_reflex.bat
```

### 2. 启动应用（跨平台）
```bash
python start_reflex.py
```

### 3. 查看日志
```bash
# 查看最后50行
python check_log.py 50

# 查看最后100行
python check_log.py 100

# 实时监控
tail -f .states/reflex_output.log
```

## 日志文件位置

`.states/reflex_output.log`

## 常见问题排查

### 编译错误
检查日志中的SyntaxError、ImportError等错误信息

### 启动失败
查看日志最后的错误堆栈信息

### 运行时错误
实时监控日志文件，捕获异常信息

## 使用场景

1. **首次启动** - 使用日志记录所有输出
2. **代码修改后** - 检查是否有编译错误
3. **调试问题** - 通过日志定位错误源头
4. **持续集成** - 自动化错误检测
