#!/bin/bash
# 启动 FactorFlow (Linux/Mac)

echo "Starting FactorFlow..."

# 激活虚拟环境
source .venv/bin/activate

# 启动后端 API
echo "Starting Backend API..."
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 启动前端
echo "Starting Frontend..."
streamlit run frontend/app.py &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo "Press Ctrl+C to stop both services"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
