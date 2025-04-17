
import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(256), unique=True, index=True)
    avatar = Column(String(256))
    first_name = Column(String(128))
    last_name = Column(String(128))
    hashed_password = Column(String(256))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    chat_data = Column(String(10000))  # 存储JSON格式的聊天记录
    # 删除了 created_at 和 updated_at 字段

    user = relationship("User", back_populates="chat_histories")

# 在 User 类中添加关系
User.chat_histories = relationship("ChatHistory", back_populates="user")


class WritingHistory(Base):
    __tablename__ = "writing_histories"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    writing_data = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    user = relationship("User", back_populates="writing_histories")

# 在User模型中添加关系
User.writing_histories = relationship("WritingHistory", back_populates="user", cascade="all, delete-orphan")
