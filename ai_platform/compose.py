"""组合根：把各模块装配成可运行的整体（依赖注入）。

单一职责：唯一的装配点。上层（gateway / CLI）只依赖 Container，不关心内部依赖关系。
作者：晨星
"""

from __future__ import annotations

from ai_platform import tools as tools_mod
from ai_platform.agent import AgentEngine
from ai_platform.config import Settings, get_settings
from ai_platform.db import init_db
from ai_platform.llm import get_llm_client
from ai_platform.memory import MemoryStore
from ai_platform.rag import RagService
from ai_platform.vectorstore import ChromaVectorStore


class Container:
    """应用容器：持有全部模块实例。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        init_db()
        self.vectorstore = ChromaVectorStore(
            self.settings.chroma_path,
            self.settings.chroma_collection,
            self.settings.embedding_dim,
        )
        self.rag = RagService(self.vectorstore, self.settings)
        self.llm = get_llm_client(self.settings)
        self.memory = MemoryStore()
        self.agent = AgentEngine(self.settings, self.llm, self.rag, self.memory, tools_mod)
