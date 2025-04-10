from typing import List, Optional

from pydantic import BaseModel


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
        orm_mode = True

class VerifyPasswordRequest(BaseModel):
    username: str
    password: str

class VerifyPasswordResponse(BaseModel):
    success: bool
