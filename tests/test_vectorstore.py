"""向量库封装单测。"""

from ai_platform.vectorstore import ChromaVectorStore


def test_add_and_search(tmp_path):
    vs = ChromaVectorStore(str(tmp_path), "unit_docs", embedding_dim=8)
    vs.add(ids=["a"], documents=["hello world"], embeddings=[[1, 0, 0, 0, 0, 0, 0, 0]])
    hits = vs.search([1, 0, 0, 0, 0, 0, 0, 0], k=1)
    assert hits and hits[0]["id"] == "a"
