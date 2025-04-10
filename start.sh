#!/bin/bash

# 获取项目根目录的绝对路径
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# 启动前端
osascript -e 'tell application "Terminal" to do script "cd '"$PROJECT_ROOT"'/frontend && npm run dev"'
echo "前端服务已启动..."

# 启动向量数据库
osascript -e 'tell application "Terminal" to do script "conda activate fastapi && cd '"$PROJECT_ROOT"'/backend_algo && chroma run --path ./data_vector_db --host localhost --port 8002"'
echo "向量数据库服务已启动..."

# 启动模型后端
osascript -e 'tell application "Terminal" to do script "conda activate fastapi && cd '"$PROJECT_ROOT"'/backend_algo && uvicorn main:app --port 8001"'
echo "模型后端服务已启动..."

# 启动业务后端
osascript -e 'tell application "Terminal" to do script "conda activate fastapi && cd '"$PROJECT_ROOT"'/backend && uvicorn main:app --port 8000"'
echo "业务后端服务已启动..."

echo "所有服务已启动完成！"
echo "- 前端: http://localhost:5173 (或npm配置的端口)"
echo "- 向量数据库: http://localhost:8002"
echo "- 模型后端: http://localhost:8001"
echo "- 业务后端: http://localhost:8000"