@echo off
REM 启动Reflex应用并记录日志
REM 日志文件: .states\reflex_output.log

REM 创建日志目录
if not exist ".states" mkdir .states

REM 获取当前时间戳
for /f "tokens=1-6 delims=/:. " %%a in ("%date% %time%") do (
    set timestamp=%%a%%b%%c%%d%%e%%f
)

REM 设置日志文件路径
set LOG_FILE=.states\reflex_output.log

REM 记录启动时间
echo ========================================== >> "%LOG_FILE%"
echo Reflex App Started at: %date% %time% >> "%LOG_FILE%"
echo ========================================== >> "%LOG_FILE%"

REM 进入trading_app目录并启动reflex，同时将输出重定向到日志文件
cd trading_app
echo Current directory: %CD% >> "..\%LOG_FILE%"
echo Running: reflex run >> "..\%LOG_FILE%"
echo. >> "..\%LOG_FILE%"

REM 启动reflex并将stdout和stderr都重定向到日志文件
reflex run >> "..\%LOG_FILE%" 2>&1

REM 如果reflex退出，记录退出时间
echo. >> "..\%LOG_FILE%"
echo ========================================== >> "..\%LOG_FILE%"
echo Reflex App Stopped at: %date% %time% >> "..\%LOG_FILE%"
echo ========================================== >> "..\%LOG_FILE%"
