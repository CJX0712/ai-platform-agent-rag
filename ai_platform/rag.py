"""RAG 检索增强模块：摄取 -> 切片 -> 向量化 -> 检索。

单一职责：知识库 ingestion 与 retrieval。向量化通过 EmbeddingProvider 接口可插拔：
默认 hash 向量（免模型下载、离线可跑）；真实场景切 sentence-transformers。
作者：晨星
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol, runtime_checkable

import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ai_platform.config import Settings


@runtime_checkable
class EmbeddingProvider(Protocol):
    """向量化接口。"""

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class HashEmbedder:
    """确定性 hash 向量：基于词项出现频率，余弦相似度可用于演示检索，无需下载模型。"""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vec = np.zeros(self.dim, dtype=np.float32)
            tokens = re.findall(r"\w+", text.lower())
            for tok in tokens:
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            out.append(vec.tolist())
        return out


class SentenceTransformerEmbedder:
    """真实文本向量化（懒加载，避免默认安装重依赖）。"""

    def __init__(self, model: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model)

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts).tolist()


class RagService:
    """检索增强服务。"""

    def __init__(self, vectorstore, settings: Settings) -> None:
        self.vectorstore = vectorstore
        self.settings = settings
        self.embedder = self._make_embedder()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

    def _make_embedder(self) -> EmbeddingProvider:
        if self.settings.embedding_provider == "sentence-transformers":
            return SentenceTransformerEmbedder(self.settings.embedding_model)
        return HashEmbedder(self.settings.embedding_dim)

    def ingest_text(self, text: str, doc_id: str, title: str = "") -> int:
        """切片 + 向量化 + 入库，返回切片数。"""
        chunks = self.splitter.split_text(text)
        if not chunks:
            return 0
        embeddings = self.embedder.embed(chunks)
        ids = [f"{doc_id}-{i}" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "title": title, "chunk": i} for i in range(len(chunks))]
        self.vectorstore.add(ids=ids, documents=chunks, embeddings=embeddings, metadatas=metadatas)
        return len(chunks)

    def retrieve(self, query: str, k: int = 4) -> list[str]:
        """向量检索，返回命中的文本片段。"""
        query_vec = self.embedder.embed([query])[0]
        hits = self.vectorstore.search(query_vec, k=k)
        return [h["document"] for h in hits]
