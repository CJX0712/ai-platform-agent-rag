# 使用指南

作者：**晨星**

## 1. 端点一览

| Method | Path | 说明 | 鉴权 |
|--------|------|------|------|
| GET | `/health` | 健康检查，返回版本/模型供给/鉴权状态 | 否 |
| POST | `/v1/chat` | 对话（自动走 Agent：工具 / 检索 / 作答） | 开启时是 |
| POST | `/v1/ingest` | 知识库摄取（文本切片 + 向量化入库） | 开启时是 |
| GET | `/v1/tools` | 列出可用工具 | 开启时是 |
| POST | `/v1/auth/token` | 演示账号换取 JWT | 需先开鉴权 |
| WS | `/ws/chat` | WebSocket 实时对话 | 同 REST |

## 2. curl 示例

```bash
# 健康
curl http://localhost:8000/health

# 摄取知识
curl -X POST http://localhost:8000/v1/ingest -H "Content-Type: application/json" \
  -d '{"title":"产品手册","text":"本平台由接入层、网关层、编排层、能力层与基础设施层组成。"}'

# 对话（会先检索知识库再作答）
curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" \
  -d '{"message":"本平台由哪几层组成？"}'

# 工具调用（安全计算器）
curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" \
  -d '{"message":"计算 23 * 47"}'

# 开启鉴权后取 token
curl -X POST http://localhost:8000/v1/auth/token -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo1234"}'
curl http://localhost:8000/v1/chat -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" -d '{"message":"你好"}'
```

响应示例：

```json
{
  "answer": "...",
  "conv_id": "2b1f0f0e-...",
  "context": ["本平台由接入层、网关层..."],
  "tool_result": ""
}
```

`conv_id` 带上下一轮即可续接多轮对话（记忆模块持久化）。

## 3. 接入真实模型

默认 `mock` 是为了**干净环境可离线跑通**。接入真实模型只改环境变量：

```bash
# 本地 Ollama
export APP_LLM_PROVIDER=ollama
export APP_LLM_BASE_URL=http://localhost:11434
export APP_LLM_MODEL=qwen2.5:3b

# 云端 OpenAI 兼容
export APP_LLM_PROVIDER=openai
export APP_LLM_BASE_URL=https://api.openai.com/v1
export APP_LLM_MODEL=gpt-4o-mini
export APP_LLM_API_KEY=sk-xxxx
```

真实语义检索（默认 hash 向量仅做演示）：

```bash
pip install ".[embeddings]"
export APP_EMBEDDING_PROVIDER=sentence-transformers
export APP_EMBEDDING_MODEL=all-MiniLM-L6-v2
```

## 4. 前端使用

直接用浏览器打开 `webui/chat.html`（零依赖，双击即可）：

1. 右上角设置里填 API 地址（默认 `http://localhost:8000`）；
2. 可在设置面板粘贴文本「摄取到知识库」；
3. 输入消息回车发送；勾选 WebSocket 则走 `/ws/chat`；
4. 回答下方「检索到的知识片段」展示 RAG 命中来源。

## 5. 扩展新工具

```python
from ai_platform import tools

class WeatherTool:
    name = "weather"
    description = "查询城市天气"
    def run(self, arg: str) -> str:
        return f"{arg} 晴 26℃"

tools.register(WeatherTool())
```

注册后即在 `/v1/tools` 可见，并在 Agent 规划中可用。

## 6. 测试与自检

```bash
python -m pytest -q        # 全量单测 + API e2e
python -m ruff check ai_platform apps tests
```
