"""配置模块单测。"""

from ai_platform.config import get_settings


def test_defaults():
    s = get_settings()
    assert s.llm_provider == "mock"
    assert s.embedding_provider == "hash"
    assert s.port == 8000


def test_env_override(monkeypatch):
    monkeypatch.setenv("APP_PORT", "9000")
    get_settings.cache_clear()
    assert get_settings().port == 9000
    get_settings.cache_clear()
