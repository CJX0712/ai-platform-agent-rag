# 系统架构

作者：**晨星**

## 1. 分层总览

```
接入层   webui/chat.html（单文件前端）          外部调用方 / SDK
   │
网关层   ai_platform/gateway（FastAPI）         鉴权 / 路由 / 限流 / WebSocket / CORS
   │
编排层   ai_platform/agent（LangGraph）         Planner → Retrieve / Tool → Answer
   │
能力层   rag（检索增强）  tools（工具集）  llm（模型供给抽象）
   │
基础设施 config  db（SQLAlchemy）  vectorstore（Chroma）  observability（日志/trace）
   │
模型供给 本地 Ollama   云端 OpenAI 兼容   离线 Mock（默认）
```

依赖方向严格**单向向下**；上层只依赖下层的 Protocol 接口，不反向依赖。装配点唯一：`ai_platform/compose.py`。

## 2. 模块职责与接口

| 模块 | 单一职责 | 关键接口 | 复用开源 | 独立验证 |
|------|----------|----------|----------|----------|
| config | 配置中心 | `Settings` / `get_settings()` | pydantic-settings | `tests/test_config.py` |
| observability | 日志 / trace 占位 | `get_logger()` / `Tracer.span()` | structlog | 启动日志无异常 |
| db | 关系存储（会话/消息/文档） | `init_db` / `get_session` | SQLAlchemy | `tests/test_db.py` |
| vectorstore | 向量库封装 | `VectorBackend.add/search` | Chroma | `tests/test_vectorstore.py` |
| llm | 模型供给抽象 | `LLMClient.chat(messages)` | httpx（Ollama/OpenAI） | `tests/test_llm.py` |
| rag | 摄取 / 切片 / 向量化 / 检索 | `RagService.ingest_text/retrieve` | LangChain 文本切分 + Chroma | `tests/test_rag.py` |
| tools | 工具注册表 | `ToolSpec.run(arg)` / `call_tool` | Python AST 安全求值 | `tests/test_tools.py` |
| memory | 会话记忆 | `MemoryStore.add/history` | SQLAlchemy | `tests/test_memory.py` |
| agent | 编排运行时 | `AgentEngine.run(msg, conv_id)` | LangGraph | `tests/test_agent.py` |
| compose | 组合根（依赖注入） | `Container` | — | 启动期装配 |
| gateway | HTTP 接入 | `create_app()` | FastAPI / slowapi / python-jose | `tests/test_api.py` |
| webui | 前端界面 | 调用 `/v1/chat`、`/ws/chat` | 原生，零依赖 | 静态校验 + 人工 |

## 3. 一次 `/v1/chat` 请求的完整链路

```
POST /v1/chat
  → gateway 鉴权（可选）→ 限流
  → Container.agent.run(message, conv_id)
      ├─ memory.add(user)                持久化用户消息
      ├─ LangGraph: plan 节点决策
      │     ├─ tool      → tools.call_tool         （如计算 23*47）
      │     ├─ retrieve  → rag.retrieve → vectorstore.search（Chroma）
      │     └─ answer    → 直接作答
      ├─ answer 节点     → llm.chat（含上下文 + 历史 + 工具结果）
      └─ memory.add(assistant)
  → ChatResponse{answer, conv_id, context, tool_result}
```

## 4. 关键技术决策

| 决策 | 选择 | 理由 | 代价 / 何时改 |
|------|------|------|----------------|
| 编排 | LangGraph StateGraph | 状态可控、条件边清晰、社区成熟 | 如需多 Agent 协作再引入 supervisor |
| 向量库 | Chroma（持久化本地目录） | 轻量、免服务、单进程即可用 | 量大 / 多实例时换 Qdrant / pgvector |
| 文本切分 | LangChain RecursiveCharacterTextSplitter | 成熟稳定、参数可控 | — |
| 模型供给 | Protocol 抽象 + mock/ollama/openai 三实现 | 干净环境可离线跑通；真实接入只改 env | 需流式输出时扩展 `stream()` |
| 默认向量化 | hash 向量 | 免下载模型，离线可复现 | 真实语义检索改 `sentence-transformers` |
| 默认模型 | mock | 无 GPU / 无 API Key 也可端到端演示 | 设 `APP_LLM_PROVIDER=ollama/openai` |
| 关系存储 | SQLite 默认，Postgres 可切 | 零依赖起步 | 并发写高时切 Postgres |
| 鉴权 | JWT，默认关闭 | 演示友好；生产一行开启 | 生产必须开并改 `APP_JWT_SECRET` |
| 工具执行 | AST 白名单，不做 `eval` | 杜绝任意代码执行风险 | 需要代码沙箱时另开独立服务 |

## 5. 可复现性与验证

- 依赖：`requirements.txt`（直接依赖）+ `requirements.lock`（`pip freeze` 全量锁定）。
- 干净环境复现：`python -m venv .venv` → `pip install -r requirements.lock` → `python -m apps.api.main`。
- 每模块均有对应单测，`pytest -q` 全绿即代表链路各段可用；`tests/test_api.py` 覆盖 REST 与 WebSocket 端到端。
- 前端为单文件 `webui/chat.html`，内联 SVG 图标（不使用 emoji 作功能图标），颜色全部走 CSS 变量。
