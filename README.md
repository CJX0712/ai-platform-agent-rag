# AI Platform · Agent + RAG

端到端可运行的 LLM 应用平台：**Agent 编排（LangGraph）+ RAG 知识库（Chroma）+ 统一模型供给 + FastAPI 网关 + 单文件前端**。
优先复用业界领先开源成果（FastAPI / LangGraph / LangChain / Chroma / SQLAlchemy），按单一职责划分 12 个可独立验证的模块。

作者：**晨星**

---

## 一句话结论

干净环境下 `pip install -r requirements.txt` → `python -m apps.api.main` → 访问 `http://localhost:8000/health` 即可跑通完整链路；
默认 `mock` 模型 + `hash` 向量，**不联网、不下载模型**即可端到端演示，切换到真实模型只改环境变量。

---

## 快速开始

```bash
# 1. 建虚拟环境并安装（Windows）
python -m venv .venv
.venv\Scripts\python -m pip install -U pip
.venv\Scripts\python -m pip install -r requirements.txt pytest==8.3.4 ruff==0.8.4

# 2. 跑测试（应全绿）
.venv\Scripts\python -m pytest -q

# 3. 启动服务
.venv\Scripts\python -m apps.api.main

# 4. 验证
curl http://localhost:8000/health
```

Docker 一键：

```bash
cp deploy/.env.example .env
docker compose -f deploy/docker-compose.yml up -d --build
curl http://localhost:8000/health
```

---

## 目录结构

```
ai-platform-agent-rag/
├─ ai_platform/            # 核心包（12 模块）
│  ├─ config.py            # 配置中心（env 驱动）
│  ├─ observability.py     # 结构化日志 / trace 占位
│  ├─ db.py                # 关系存储（SQLAlchemy）
│  ├─ vectorstore.py       # 向量库封装（Chroma）
│  ├─ llm.py               # 模型供给抽象（mock/ollama/openai）
│  ├─ rag.py               # 摄取 / 切片 / 向量化 / 检索
│  ├─ tools.py             # 工具注册表 + 内置工具
│  ├─ memory.py            # 会话记忆
│  ├─ agent.py             # Agent 编排（LangGraph）
│  ├─ compose.py           # 组合根（依赖注入）
│  └─ gateway/             # API 网关（路由/鉴权/限流/WS）
├─ apps/api/main.py        # 服务入口
├─ webui/chat.html         # 单文件前端（零依赖）
├─ tests/                  # 各模块单测 + API e2e
├─ deploy/                 # Dockerfile / compose / .env.example / 云部署脚本
├─ docs/                   # ARCHITECTURE / DEPLOYMENT / USAGE
├─ requirements.txt        # 直接依赖
└─ requirements.lock       # 锁定全量依赖（可复现构建）
```

---

## 文档

| 文档 | 内容 |
|------|------|
| `docs/ARCHITECTURE.md` | 系统架构、模块职责与接口、调用关系、技术决策 |
| `docs/DEPLOYMENT.md` | 本地 / Docker / 云服（FRP）部署、环境变量、回滚、排障 |
| `docs/USAGE.md` | API 调用示例、接入真实模型、前端使用 |

---

## 实测状态（Windows 11 / Python 3.13 / Docker 29）

| 验证项 | 结果 |
|--------|------|
| 单元测试（pytest） | 18/18 通过 |
| 静态检查（ruff） | 全部通过 |
| 裸机端到端（scripts/e2e_check.py） | 7/7 通过 |
| Docker 构建 | 成功（`ai-platform-agent-rag:0.1.0`） |
| 容器内端到端 | 7/7 通过 |

端到端覆盖：健康检查、工具清单、知识摄取、**RAG 检索命中原文**、**工具调用（123*45+6=5541）**、参数缺失 422、WebSocket 实时对话。

License: MIT
