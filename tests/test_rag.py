"""RAG 模块单测。"""

from ai_platform.config import get_settings
from ai_platform.rag import RagService
from ai_platform.vectorstore import ChromaVectorStore


def test_ingest_and_retrieve(tmp_path):
    vs = ChromaVectorStore(str(tmp_path), "rag", embedding_dim=get_settings().embedding_dim)
    rag = RagService(vs, get_settings())
    text = "量子计算利用叠加与纠缠实现并行计算。光子芯片可提升互联带宽。"
    n = rag.ingest_text(text, "doc-rag")
    assert n >= 1
    hits = rag.retrieve("量子计算 叠加", k=2)
    assert any("量子计算" in h for h in hits)
