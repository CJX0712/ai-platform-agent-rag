"""模型供给单测（mock 路径，免联网）。"""

from ai_platform.config import get_settings
from ai_platform.llm import MockLLMClient, get_llm_client


def test_mock_reply():
    c = MockLLMClient(get_settings())
    assert "离线演示" in c.chat([{"role": "user", "content": "hi"}])


def test_factory_returns_mock():
    assert isinstance(get_llm_client(get_settings()), MockLLMClient)
