#!/bin/bash

# 获取项目根目录的绝对路径
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "正在关闭 paper_writing_helper 的所有服务..."

# 关闭前端服务 (npm run dev)
echo "正在关闭前端服务..."
pkill -f "node.*vite"

# 关闭业务后端服务 (uvicorn main:app --port 8000)
echo "正在关闭业务后端服务..."
pkill -f "uvicorn main:app --port 8000"
# 等待业务后端完全关闭
sleep 2

# 关闭模型后端服务 (uvicorn main:app --port 8001)
echo "正在关闭模型后端服务..."
# 先尝试清空向量数据库
echo "尝试清空向量数据库..."
curl -X POST "http://localhost:8001/clear_vectordb" || echo "清空向量数据库失败，将直接关闭服务"
sleep 1
# 关闭模型后端
pkill -f "uvicorn main:app --port 8001"
# 等待模型后端完全关闭
sleep 2

# 最后关闭向量数据库服务 (chroma)
echo "正在关闭向量数据库服务..."
pkill -f "chroma run"

echo "所有服务已关闭！"