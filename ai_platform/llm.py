"""模型供给抽象模块：本地 / 云端统一接口。

单一职责：把不同 LLM 供给方（离线 Mock / Ollama / OpenAI 兼容）收敛为统一 chat 接口，
上层编排与供给方解耦。真实接入只需在 .env 切换 APP_LLM_PROVIDER。
作者：晨星
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import httpx

from ai_platform.config import Settings, get_settings


@runtime_checkable
class LLMClient(Protocol):
    """统一的聊天接口。"""

    def chat(self, messages: list[dict], **kwargs) -> str: ...


class MockLLMClient:
    """离线演示客户端：不联网、不下载模型，返回确定性回复，保证干净环境可运行。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def chat(self, messages: list[dict], **kwargs) -> str:
        last = messages[-1]["content"] if messages else ""
        return (
            "[离线演示] 当前为 mock 模型，未接入真实大模型。\n"
            f"已收到问题摘要：{last[:120]}\n"
            "如需真实推理，请设置 APP_LLM_PROVIDER=ollama 或 openai 并配置 APP_LLM_BASE_URL。"
        )


class OllamaClient:
    """Ollama 本地推理客户端（REST /api/chat）。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def chat(self, messages: list[dict], **kwargs) -> str:
        url = self.settings.llm_base_url.rstrip("/") + "/api/chat"
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": self.settings.llm_temperature},
        }
        resp = httpx.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json()["message"]["content"]


class OpenAIClient:
    """OpenAI 兼容客户端（任意兼容 /v1/chat/completions 的服务）。"""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def chat(self, messages: list[dict], **kwargs) -> str:
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.settings.llm_model,
            "messages": messages,
            "temperature": self.settings.llm_temperature,
        }
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"} if self.settings.llm_api_key else {}
        resp = httpx.post(url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    """按配置返回对应供给客户端。"""
    settings = settings or get_settings()
    provider = settings.llm_provider.lower()
    if provider == "ollama":
        return OllamaClient(settings)
    if provider == "openai":
        return OpenAIClient(settings)
    return MockLLMClient(settings)
