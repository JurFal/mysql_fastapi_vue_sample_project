from typing import List, Optional

from pydantic import BaseModel

import datetime
from typing import Optional # 导入 Optional

class UserBase(BaseModel):
    username: str
    email: str
    avatar: Optional[str] = None
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    is_active: bool
    is_superuser: bool

    class Config:
        # orm_mode = True
        from_attributes = True

class UserList(BaseModel):
    total: int
    users: List[User]


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    response: str


# 在现有的 schemas.py 文件中添加以下类

class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    avatar: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_active: bool | None = None
    
    class Config:
        from_attributes = True  # 替换 orm_mode = True

class VerifyPasswordRequest(BaseModel):
    username: str
    password: str

class VerifyPasswordResponse(BaseModel):
    success: bool


class ChatHistoryBase(BaseModel):
    chat_data: str

class ChatHistoryCreate(ChatHistoryBase):
    pass

class ChatHistory(ChatHistoryBase):
    id: int
    user_id: int
    # 删除了 created_at 和 updated_at 字段

    class Config:
        from_attributes = True  # 替换 orm_mode = True


class UsernameRequest(BaseModel):
    username: str

class UserID(BaseModel):
    id: int


class WritingHistoryBase(BaseModel):
    writing_data: str


class WritingHistoryCreate(WritingHistoryBase):
    pass


class WritingHistory(WritingHistoryBase):
    id: int
    user_id: int
    # 将类型改为 Optional[datetime.datetime] 以允许 None
    created_at: Optional[datetime.datetime]
    updated_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True # Replaces orm_mode=True in Pydantic v2


class WritingHistoryList(BaseModel):
    total: int
    writing_histories: list[WritingHistory]
