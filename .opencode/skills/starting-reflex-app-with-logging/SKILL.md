---
name: starting-reflex-app-with-logging
description: Use when starting Reflex applications and needing to monitor for compilation errors, startup failures, or runtime issues through centralized logs
---

# Starting Reflex App with Logging

## Overview
Automated startup scripts for Reflex applications that capture all output to centralized log files for error detection and debugging.

**Core principle:** Always use logging to capture startup and runtime errors, never rely on console output alone.

## When to Use
- Starting a Reflex application for the first time
- After making code changes that might cause compilation errors
- When debugging startup issues
- When monitoring application health

## Quick Reference

| Task | Command |
|------|---------|
| Start app (Windows) | `start_reflex.bat` |
| Start app (Unix/Mac) | `python start_reflex.py` |
| Check logs (last 50 lines) | `python check_log.py 50` |
| Monitor logs in real-time | `tail -f logs/reflex_output.log` |
| Check for errors | `grep -i error logs/reflex_output.log` |

## Log File Location
- **Path:** `logs/reflex_output.log`
- **Format:** Plain text with timestamps
- **Content:** stdout + stderr from Reflex process

## Startup Scripts

### Windows (start_reflex.bat)
```batch
@echo off
start_reflex.bat
```
Captures all output to `logs\reflex_output.log`

### Universal (start_reflex.py)
```bash
python start_reflex.py
```
Works on all platforms, real-time logging with console output.

## Common Issues and Solutions

### Compilation Errors
**Symptoms:** SyntaxError, ImportError, ModuleNotFoundError in logs
**Solution:** 
1. Check log file for exact error location
2. Fix code issues
3. Restart application

### Startup Failures
**Symptoms:** "Process granian-worker: Traceback", application exits immediately
**Solution:**
1. Check last 100 lines of log: `python check_log.py 100`
2. Look for missing dependencies or configuration issues
3. Verify environment variables

### Runtime Errors
**Symptoms:** Errors appear in logs after startup
**Solution:**
1. Monitor logs in real-time: `tail -f .states/reflex_output.log`
2. Check for recurring patterns
3. Add error handling or fix root cause

## Log Analysis Commands

### Quick Health Check
```bash
# Check last 50 lines
python check_log.py 50

# Look for errors
grep -i "error\|exception\|failed" logs/reflex_output.log

# Check startup success
grep "App running" logs/reflex_output.log
```

### Detailed Analysis
```bash
# All errors with context
grep -A 5 -B 5 "Error" logs/reflex_output.log

# Count error types
grep -i "error" logs/reflex_output.log | wc -l
```

## Best Practices
1. **Always check logs after startup** - Don't assume success
2. **Monitor logs during development** - Catch issues early
3. **Archive old logs** - Keep history for debugging
4. **Set log rotation** - Prevent huge log files

## Integration with Development Workflow
1. Make code changes
2. Start app with logging: `python start_reflex.py`
3. Check logs for errors: `python check_log.py 50`
4. Fix any issues
5. Verify fix in logs
