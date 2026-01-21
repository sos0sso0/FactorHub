@echo off
REM FactorFlow 启动脚本
REM 新架构：直接调用模式，只需启动 Streamlit

echo ====================================
echo   FactorFlow - 因子分析平台
echo ====================================
echo.
echo 正在启动 Streamlit 前端...
echo 后端服务将以直接调用模式运行
echo.

cd /d "%~dp0"

REM 启动 Streamlit
streamlit run frontend/app.py

pause
