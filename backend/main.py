from datetime import datetime, timedelta, timezone
from typing import Annotated
import subprocess
import time
import os

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from sqlalchemy.orm import Session
import sqlalchemy.exc

import crud, models, schemas
from database import SessionLocal, engine
from security import verify_password

import requests
from fastapi import FastAPI
from proxy import router as proxy_router

app = FastAPI()


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 999


# 尝试启动 MySQL 服务
def ensure_mysql_running():
    try:
        # 尝试创建一个测试连接
        test_engine = engine.connect()
        test_engine.close()
        print("MySQL 服务已经在运行")
    except sqlalchemy.exc.OperationalError:
        print("MySQL 服务未运行，尝试启动...")
        try:
            subprocess.run(["brew", "services", "start", "mysql"], check=True)
            print("MySQL 服务启动命令已执行，等待服务启动...")
            time.sleep(10)  # 给 MySQL 一些启动时间
            
            # 再次尝试连接
            for i in range(5):
                try:
                    test_engine = engine.connect()
                    test_engine.close()
                    print("MySQL 服务已成功启动")
                    return
                except sqlalchemy.exc.OperationalError:
                    print(f"等待 MySQL 启动... 尝试 {i+1}/5")
                    time.sleep(5)
            
            print("无法启动 MySQL 服务，请手动检查")
        except subprocess.CalledProcessError:
            print("启动 MySQL 服务失败，请确保已安装 MySQL 并有足够权限")
        except Exception as e:
            print(f"启动 MySQL 时发生错误: {e}")


# 在应用启动前确保 MySQL 运行
ensure_mysql_running()

# 创建数据库表
try:
    models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"创建数据库表时出错: {e}")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Dependency
def get_session():
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta # 修改这里
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) # 修改这里
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token( # 调用 create_access_token
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    return current_user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: SessionDep):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=schemas.UserList)
async def read_users(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return schemas.UserList(total=crud.count_users(db), users=users)


@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        user_id: int,
        db: SessionDep
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        user_id: int,
        db: SessionDep
):

    # 检查用户是否存在
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户
    crud.delete_user(db, user_id=user_id)
    return None  # 204状态码不需要返回内容


@app.get("/users/name/{username}", response_model=schemas.User)
async def read_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        username: str,
        db: SessionDep
):
    # print(current_user.username)
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.delete("/users/name/{username}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_username(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        username: str,
        db: SessionDep
):
    # 可以添加权限检查，例如只允许管理员或用户自己删除
    # if not current_user.is_admin and current_user.username != username:
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="没有足够权限执行此操作"
    #    )
    
    # 检查用户是否存在
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 删除用户
    crud.delete_user_by_username(db, username=username)
    return None


@app.put("/users/name/{username}", response_model=schemas.User)
async def update_user_by_username(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        username: str,
        user_update: schemas.UserUpdate,
        db: SessionDep
):
    # 可以添加权限检查，例如只允许管理员或用户自己更新
    # if not current_user.is_admin and current_user.username != username:
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="没有足够权限执行此操作"
    #    )
    
    # 检查用户是否存在
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 更新用户信息
    updated_user = crud.update_user_by_username(db, username=username, user_update=user_update)
    if updated_user is None:
        raise HTTPException(status_code=500, detail="更新用户信息失败")
    
    return updated_user


@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatRequest
):
    # print(current_user.username)
    resp = requests.post('http://localhost:8001/chat', json={
        'messages': [
            {
                'role': 'user',
                'content': chat_request.prompt,
            }
        ]
    })
    return schemas.ChatResponse(response=resp.json()['choices'][0]['message']['content'])


# 注册代理路由
app.include_router(proxy_router, prefix="/proxy")


@app.post("/verify-password", response_model=schemas.VerifyPasswordResponse)
async def verify_password_endpoint(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    verify_request: schemas.VerifyPasswordRequest,
    db: SessionDep
):
    # 只允许验证自己的密码
    # if current_user.username != verify_request.username:
    #    raise HTTPException(
    #        status_code=status.HTTP_403_FORBIDDEN,
    #        detail="只能验证自己的密码"
    #    )
    
    # 验证密码
    user = authenticate_user(db, verify_request.username, verify_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="密码验证失败"
        )
    
    return schemas.VerifyPasswordResponse(success=True)


@app.post("/save/chat/", response_model=schemas.ChatHistory)
async def save_chat_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    chat_data: schemas.ChatHistoryCreate,
    db: SessionDep
):
    # 检查用户是否已有聊天历史
    existing_history = crud.get_chat_history(db, current_user.id)
    
    if existing_history:
        # 更新现有聊天历史
        updated_history = crud.update_chat_history(db, current_user.id, chat_data.chat_data)
        if updated_history is None:
            raise HTTPException(status_code=500, detail="更新聊天历史失败")
        return updated_history
    else:
        # 创建新的聊天历史
        return crud.create_chat_history(db, current_user.id, chat_data.chat_data)


@app.get("/get/chat/", response_model=schemas.ChatHistory)
async def get_chat_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # 获取用户的聊天历史
    chat_history = crud.get_chat_history(db, current_user.id)
    if not chat_history:
        raise HTTPException(status_code=404, detail="聊天历史不存在")
    return chat_history


@app.delete("/delete/chat/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # 删除用户的聊天历史
    result = crud.delete_chat_history(db, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="聊天历史不存在")
    return None  # 204状态码不需要返回内容


@app.post("/users/id-by-username/", response_model=schemas.UserID)
async def get_user_id_by_username(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    username_request: schemas.UsernameRequest,
    db: SessionDep
):
    db_user = crud.get_user_by_username(db, username=username_request.username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"id": db_user.id}


@app.post("/save/writing/", response_model=schemas.WritingHistory)
async def save_writing_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    writing_data: schemas.WritingHistoryCreate,
    db: SessionDep
):
    # 检查用户是否已有写作历史
    existing_history = crud.get_writing_history(db, current_user.id)
    
    if existing_history:
        # 更新现有写作历史
        updated_history = crud.update_writing_history(db, current_user.id, writing_data.writing_data)
        if updated_history is None:
            raise HTTPException(status_code=500, detail="更新写作历史失败")
        return updated_history
    else:
        # 创建新的写作历史
        return crud.create_writing_history(db, current_user.id, writing_data.writing_data)


@app.get("/get/writing/", response_model=schemas.WritingHistory)
async def get_writing_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # 获取用户的写作历史
    writing_history = crud.get_writing_history(db, current_user.id)
    if not writing_history:
        raise HTTPException(status_code=404, detail="写作历史不存在")
    return writing_history


@app.get("/list/writings/", response_model=schemas.WritingHistoryList)
async def list_writing_histories(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 100
):
    # 获取用户的所有写作历史列表
    writing_histories = crud.get_all_writing_histories(db, user_id=current_user.id, skip=skip, limit=limit)
    total = crud.count_writing_histories(db, user_id=current_user.id)
    return schemas.WritingHistoryList(total=total, writing_histories=writing_histories)


@app.post("/create/writing/", response_model=schemas.WritingHistory)
async def create_writing_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    writing_data: schemas.WritingHistoryCreate,
    db: SessionDep
):
    # 创建新的写作历史
    return crud.create_writing_history(db, current_user.id, writing_data.writing_data)


@app.delete("/delete/writing/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_writing_history(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    # 删除用户的写作历史
    result = crud.delete_writing_history(db, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="写作历史不存在")
    return None  # 204状态码不需要返回内容


# 后端API实现

@app.get("/get/writing/all/", response_model=list[schemas.WritingHistory])
async def get_all_writing_histories(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 100
):
    """获取当前用户的所有写作历史记录"""
    # 获取用户的所有写作历史
    writing_histories = crud.get_all_writing_histories_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    if not writing_histories:
        return []
    return writing_histories


@app.delete("/delete/writing/{writing_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_writing_history_by_id(
    writing_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """删除指定ID的写作历史记录"""
    # 删除指定ID的写作历史，并验证该历史属于当前用户
    result = crud.delete_writing_history_by_id(db, writing_id, current_user.id)
    if not result:
        raise HTTPException(status_code=404, detail="写作历史不存在或无权限删除")
    return None  # 204状态码不需要返回内容


@app.put("/update/writing/{writing_id}/", response_model=schemas.WritingHistory)
async def update_writing_history_by_id(
    writing_id: int,
    writing_data: schemas.WritingHistoryCreate,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """更新指定ID的写作历史记录"""
    # 更新指定ID的写作历史，并验证该历史属于当前用户
    updated_history = crud.update_writing_history_by_id(db, writing_id, current_user.id, writing_data.writing_data)
    if updated_history is None:
        raise HTTPException(status_code=404, detail="写作历史不存在或无权限更新")
    return updated_history


@app.get("/get/writing/{writing_id}/", response_model=schemas.WritingHistory)
async def get_writing_history_by_id(
    writing_id: int,
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep
):
    """根据ID获取指定写作历史记录"""
    writing_history = crud.get_writing_history_by_id(db, writing_id, current_user.id)
    if not writing_history:
        raise HTTPException(status_code=404, detail="写作历史不存在或无权限访问")
    return writing_history

