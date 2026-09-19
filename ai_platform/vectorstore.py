"""向量库封装模块：Chroma 持久化。

单一职责：对向量数据库的读写做一层稳定接口，屏蔽具体实现。
接口 VectorBackend 可替换为 FAISS / Qdrant 等而不影响上层。
作者：晨星
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class VectorBackend(Protocol):
    """向量存储统一接口。"""

    def add(self, ids, documents, embeddings, metadatas=None) -> None: ...

    def search(self, query_embedding, k: int = 4): ...


def _validate_collection_name(name: str) -> str:
    """Chroma 1.x 约束：3-512 字符，仅 [a-zA-Z0-9._-]，首尾为字母或数字。"""
    import re

    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{1,510}[a-zA-Z0-9]", name or ""):
        raise ValueError(
            f"非法集合名 {name!r}：需 3-512 字符，仅含 [a-zA-Z0-9._-]，且首尾为字母或数字"
        )
    return name


class ChromaVectorStore:
    """基于 Chroma 的持久化向量存储实现。"""

    def __init__(self, path: str, collection_name: str, embedding_dim: int = 256) -> None:
        import chromadb

        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(
            name=_validate_collection_name(collection_name), metadata={"hnsw:space": "cosine"}
        )
        self.embedding_dim = embedding_dim

    def add(self, ids, documents, embeddings, metadatas=None) -> None:
        n = len(documents)
        # Chroma 要求 metadata 为非空字典，缺省时补充 source 字段
        metas = metadatas or [{"source": "unknown"} for _ in range(n)]
        metas = [m if m else {"source": "unknown"} for m in metas]
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metas,
        )

    def search(self, query_embedding, k: int = 4):
        res = self.collection.query(query_embeddings=[query_embedding], n_results=k)
        out = []
        docs = res.get("documents") or [[]]
        ids = res.get("ids") or [[]]
        dist = res.get("distances") or [[]]
        metas = res.get("metadatas") or [[]]
        for i, doc in enumerate(docs[0]):
            out.append(
                {
                    "id": ids[0][i],
                    "document": doc,
                    "score": dist[0][i],
                    "metadata": metas[0][i],
                }
            )
        return out
