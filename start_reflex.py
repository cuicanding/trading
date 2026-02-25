#!/usr/bin/env python3
"""
启动Reflex应用并记录日志
日志文件: .states/reflex_output.log
"""
import os
import sys
import subprocess
import signal
from datetime import datetime
from pathlib import Path
import json

PID_FILE = "logs/reflex.pid"
LOG_FILE = "logs/reflex_output.log"

def is_running():
    """检查进程是否在运行"""
    pid_file = Path(__file__).parent / "logs" / "reflex.pid"
    if not pid_file.exists():
        return False
    
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        # 检查进程是否存在（Windows兼容）
        try:
            import psutil
            return psutil.pid_exists(pid)
        except ImportError:
            # 如果没有psutil，使用简单的方法
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True
            )
            return str(pid) in result.stdout
    except (OSError, ValueError, FileNotFoundError):
        return False

def stop_app():
    """停止应用"""
    pid_file = Path(PID_FILE)
    if pid_file.exists():
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"✓ 已停止进程 {pid}")
            pid_file.unlink()
        except (OSError, ValueError, ProcessLookupError) as e:
            print(f"停止失败: {e}")
            if pid_file.exists():
                pid_file.unlink()

def start_app():
    """启动应用"""
    if is_running():
        print("⚠️  应用已在运行中")
        print(f"日志文件: {LOG_FILE}")
        print(f"访问地址: http://localhost:3000/")
        return
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # 创建日志目录
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "reflex_output.log"
    pid_file = log_dir / "reflex.pid"
    
    # 记录启动信息
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write("\n" + "=" * 60 + "\n")
        f.write(f"Reflex App Started at: {timestamp}\n")
        f.write(f"Working Directory: {os.getcwd()}\n")
        f.write("=" * 60 + "\n\n")
    
    print("🚀 Starting Reflex app...")
    print(f"📝 Log file: {log_file}")
    print(f"🌐 Will be available at: http://localhost:3000/")
    print(f"📊 Backend: http://localhost:8000/")
    print()
    
    # 启动reflex进程
    try:
        # Windows下使用shell重定向
        if os.name == 'nt':
            # Windows: 使用shell重定向
            cmd = f'"{sys.executable}" -m reflex run >> "{log_file}" 2>&1'
            process = subprocess.Popen(
                cmd,
                cwd=project_root,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Unix/Linux: 使用subprocess重定向
            log_handle = open(log_file, "a", encoding="utf-8")
            process = subprocess.Popen(
                [sys.executable, "-m", "reflex", "run"],
                cwd=project_root,
                stdout=log_handle,
                stderr=log_handle,
                start_new_session=True
            )
        
        # 保存PID
        with open(pid_file, "w") as pf:
            pf.write(str(process.pid))
        
        # 等待一段时间让应用启动
        import time
        print("⏳ Waiting for app to start...")
        time.sleep(8)
        
        # 检查进程是否还在运行
        if is_running():
            print(f"✓ 应用已启动 (PID: {process.pid})")
            print(f"✓ 前端: http://localhost:3000/")
            print(f"✓ 后端: http://localhost:8000/")
            print()
            print("📋 查看日志: python check_log.py 50")
            print("🛑 停止应用: python start_reflex.py --stop")
            print()
            print("💡 应用正在后台运行，关闭此终端不会停止应用")
        else:
            print("✗ 应用启动失败，请检查日志")
            print(f"  查看日志: cat {log_file}")
                
    except Exception as e:
        print(f"✗ 启动失败: {e}")
        sys.exit(1)

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stop":
            stop_app()
        elif sys.argv[1] == "--status":
            if is_running():
                print("✓ 应用正在运行")
                print(f"  前端: http://localhost:3000/")
                print(f"  后端: http://localhost:8000/")
            else:
                print("✗ 应用未运行")
        else:
            print(f"未知命令: {sys.argv[1]}")
            print("用法:")
            print("  python start_reflex.py         # 启动应用")
            print("  python start_reflex.py --stop  # 停止应用")
            print("  python start_reflex.py --status # 查看状态")
    else:
        start_app()

if __name__ == "__main__":
    main()
