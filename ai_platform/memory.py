"""会话记忆模块：基于关系库的多轮对话持久化。

单一职责：管理会话与消息的读写，为 Agent 提供历史上下文。
作者：晨星
"""

from __future__ import annotations

import uuid

from ai_platform.db import Conversation, Message, get_session


class MemoryStore:
    """会话记忆存储。"""

    def new_conversation(self, title: str = "") -> str:
        cid = str(uuid.uuid4())
        with get_session() as s:
            s.add(Conversation(id=cid, title=title))
            s.commit()
        return cid

    def ensure(self, conv_id: str) -> None:
        with get_session() as s:
            if s.get(Conversation, conv_id) is None:
                s.add(Conversation(id=conv_id))
                s.commit()

    def add(self, conv_id: str, role: str, content: str) -> None:
        with get_session() as s:
            s.add(Message(conv_id=conv_id, role=role, content=content))
            s.commit()

    def history(self, conv_id: str, k: int = 20) -> list[dict]:
        with get_session() as s:
            rows = s.query(Message).filter_by(conv_id=conv_id).order_by(Message.id).all()
        msgs = [{"role": m.role, "content": m.content} for m in rows]
        return msgs[-k:] if k else msgs
