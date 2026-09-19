"""关系存储模块：SQLAlchemy 2.x。

单一职责：管理会话/消息/文档元数据的持久化。向量数据在 vectorstore 模块。
作者：晨星
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from ai_platform.config import get_settings

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True)
    title = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conv_id = Column(String, ForeignKey("conversations.id"), index=True)
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class Document(Base):
    __tablename__ = "documents"
    id = Column(String, primary_key=True)
    title = Column(String)
    source = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        url = get_settings().database_url
        # SQLAlchemy 2.x：SQLite 的驱动参数必须走 connect_args，不能直传 create_engine
        kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {}
        _engine = create_engine(url, future=True, **kwargs)
    return _engine


def init_db() -> None:
    """建表（幂等）。"""
    Base.metadata.create_all(get_engine())


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _SessionLocal()
