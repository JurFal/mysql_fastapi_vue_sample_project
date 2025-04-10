# 后端（业务层）：FastAPI

## 环境

后端使用conda管理环境：
```shell
conda create -n fastapi python=3.12
pip install -r requirements.txt
```

## 数据库

本项目使用MySQL数据库，连接字符串在`database.py`文件中配置，表结构（`CREATE TABLE`）会在程序启动时自动创建。

## 启动

启动：
```shell
uvicorn main:app --port 8000
```

文档页面：`http://127.0.0.1:8000/docs`
