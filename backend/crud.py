from sqlalchemy.orm import Session
from datetime import datetime  # 添加datetime导入

import models, schemas

from security import get_password_hash


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def count_users(db: Session):
    return db.query(models.User).count()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        avatar=user.avatar,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def delete_user_by_username(db: Session, username: str):
    db_user = get_user_by_username(db, username)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


def update_user_by_username(db: Session, username: str, user_update: schemas.UserUpdate):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    # 如果更新包含密码，需要对其进行哈希处理
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def get_chat_history(db: Session, user_id: int):
    return db.query(models.ChatHistory).filter(models.ChatHistory.user_id == user_id).first()


def create_chat_history(db: Session, user_id: int, chat_data: str):
    db_chat_history = models.ChatHistory(user_id=user_id, chat_data=chat_data)
    db.add(db_chat_history)
    db.commit()
    db.refresh(db_chat_history)
    return db_chat_history


def update_chat_history(db: Session, user_id: int, chat_data: str):
    db_chat_history = get_chat_history(db, user_id)
    if db_chat_history:
        db_chat_history.chat_data = chat_data
        # 删除了 updated_at 时间戳更新
        db.commit()
        db.refresh(db_chat_history)
        return db_chat_history
    return None


def delete_chat_history(db: Session, user_id: int):
    db_chat_history = get_chat_history(db, user_id)
    if db_chat_history:
        db.delete(db_chat_history)
        db.commit()
        return True
    return False


def get_writing_history(db: Session, user_id: int):
    return db.query(models.WritingHistory).filter(models.WritingHistory.user_id == user_id).first()


def create_writing_history(db: Session, user_id: int, writing_data: str):
    db_writing_history = models.WritingHistory(user_id=user_id, writing_data=writing_data)
    db.add(db_writing_history)
    db.commit()
    db.refresh(db_writing_history)
    return db_writing_history


def update_writing_history(db: Session, user_id: int, writing_data: str):
    db_writing_history = get_writing_history(db, user_id)
    if db_writing_history:
        db_writing_history.writing_data = writing_data
        # 删除了 updated_at 时间戳更新
        db.commit()
        db.refresh(db_writing_history)
        return db_writing_history
    return None


def delete_writing_history(db: Session, user_id: int):
    db_writing_history = get_writing_history(db, user_id)
    if db_writing_history:
        db.delete(db_writing_history)
        db.commit()
        return True
    return False


def get_all_writing_histories_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户的所有写作历史记录"""
    return db.query(models.WritingHistory).filter(models.WritingHistory.user_id == user_id).offset(skip).limit(limit).all()


def delete_writing_history_by_id(db: Session, writing_id: int, user_id: int):
    """删除指定ID的写作历史记录，并验证该历史属于指定用户"""
    writing_history = db.query(models.WritingHistory).filter(
        models.WritingHistory.id == writing_id,
        models.WritingHistory.user_id == user_id
    ).first()
    
    if not writing_history:
        return False
    
    db.delete(writing_history)
    db.commit()
    return True


def get_writing_history_by_id(db: Session, writing_id: int, user_id: int):
    """根据ID和用户ID获取指定写作历史记录"""
    return db.query(models.WritingHistory).filter(
        models.WritingHistory.id == writing_id,
        models.WritingHistory.user_id == user_id
    ).first()


def update_writing_history_by_id(db: Session, writing_id: int, user_id: int, writing_data: str):
    """更新指定ID的写作历史记录，并验证该历史属于指定用户"""
    writing_history = db.query(models.WritingHistory).filter(
        models.WritingHistory.id == writing_id,
        models.WritingHistory.user_id == user_id
    ).first()
    
    if not writing_history:
        return None
    
    writing_history.writing_data = writing_data
    writing_history.updated_at = datetime.now()  # 现在可以正确使用datetime
    db.commit()
    db.refresh(writing_history)
    return writing_history

def count_writing_histories(db: Session, user_id: int):
    """计算用户的写作历史总数"""
    return db.query(models.WritingHistory).filter(models.WritingHistory.user_id == user_id).count()
