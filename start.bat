@echo off
setlocal

cd /d "%~dp0backend"

echo ==========================================
echo   AI 简历教练 - 一键启动
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境 .venv
    echo 请先在 backend 目录执行：
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist ".env" (
    echo [错误] 未找到 .env 配置文件
    echo 请复制 .env.example 为 .env，并填入 DEEPSEEK_API_KEY
    echo.
    pause
    exit /b 1
)

echo 正在启动后端服务...
start "AI简历教练-后端" .venv\Scripts\python.exe app.py

echo 等待服务就绪...
timeout /t 3 /nobreak >nul

echo 正在打开浏览器...
start "" http://127.0.0.1:8000

echo.
echo 服务已启动！
echo   访问地址：http://127.0.0.1:8000
echo   停止服务：关闭「AI简历教练-后端」窗口
echo.
pause
endlocal
