"""Agent 编排端到端（mock 模型，离线可跑）。"""

from ai_platform.compose import Container
from ai_platform.config import get_settings


def test_agent_calculator(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_CHROMA_PATH", str(tmp_path))
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///" + str(tmp_path / "a.db"))
    get_settings.cache_clear()
    c = Container()
    res = c.agent.run("请帮我计算 23 * 47")
    assert "1081" in res["tool_result"]
    assert res["answer"]


def test_agent_rag(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_CHROMA_PATH", str(tmp_path))
    monkeypatch.setenv("APP_DATABASE_URL", "sqlite:///" + str(tmp_path / "a.db"))
    get_settings.cache_clear()
    c = Container()
    c.rag.ingest_text("草莓是多年生草本植物，果实富含维生素C。", "doc-berry", "berry")
    res = c.agent.run("草莓含有什么维生素？")
    assert res["context"] and any("维生素" in x for x in res["context"])
    assert res["answer"]
