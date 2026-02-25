#!/usr/bin/env python3
"""
查看Reflex应用日志
"""
import sys
from pathlib import Path

def tail_log(lines=50):
    """查看日志最后N行"""
    log_file = Path(__file__).parent / "logs" / "reflex_output.log"
    
    if not log_file.exists():
        print(f"Log file not found: {log_file}")
        return
    
    with open(log_file, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
        last_lines = all_lines[-lines:]
        
        for line in last_lines:
            print(line, end='')

if __name__ == "__main__":
    lines = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    tail_log(lines)
