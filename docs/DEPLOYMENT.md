# 部署指南

作者：**晨星**

## 1. 本地裸机（最快验证）

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.lock     # Windows
# Linux/macOS: .venv/bin/python -m pip install -r requirements.lock

cp deploy/.env.example .env        # 按需修改
python -m apps.api.main
curl http://localhost:8000/health  # 期望 {"status":"ok",...}
```

## 2. Docker / Compose（推荐）

```bash
cp deploy/.env.example .env
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f api
curl http://localhost:8000/health
docker compose -f deploy/docker-compose.yml down
```

- 数据卷：宿主机 `./data` 挂载到容器 `/app/data`（Chroma 与 SQLite 落盘，重启不丢）。
- 健康检查：内置 `HEALTHCHECK` 每 30s 访问 `/health`。
- 首次构建会拉全量依赖，约 1–3 分钟（取决于网络）。

## 3. 云服部署（FRP / SSH）

```bash
SSH_HOST=43.161.233.163 SSH_USER=root SSH_PORT=22 ./deploy/cloud-deploy.sh
```

脚本做四件事：rsync 同步代码 → 生成 `.env` → `docker compose up -d --build` → 校验 `http://127.0.0.1:8000/health`。
若通过 FRP 将容器内 8000 映射到公网端口，公网访问 `http://<公网IP>:<端口>/health` 即可。

## 4. 环境变量

| 变量 | 默认 | 说明 |
|------|------|------|
| `APP_LLM_PROVIDER` | `mock` | `mock` / `ollama` / `openai` |
| `APP_LLM_BASE_URL` | `http://localhost:11434` | Ollama 或 OpenAI 兼容服务地址 |
| `APP_LLM_MODEL` | `qwen2.5:3b` | 模型名 |
| `APP_LLM_API_KEY` | 空 | 云端服务密钥 |
| `APP_EMBEDDING_PROVIDER` | `hash` | `hash` / `sentence-transformers` |
| `APP_AUTH_ENABLED` | `false` | 生产建议 `true` |
| `APP_JWT_SECRET` | `dev-secret-change-me` | 生产必须更换 |
| `APP_RATE_LIMIT_PER_MIN` | `60` | 每 IP 每分钟请求数 |
| `APP_CHROMA_PATH` | `./data/chroma` | 向量库目录 |
| `APP_DATABASE_URL` | `sqlite:///./data/app.db` | 关系库连接串 |

## 5. 回滚与运维

- 回滚：`docker compose down` → 切回上一个镜像 tag → `docker compose up -d`；镜像按 `0.1.0` 打 tag，建议保留上一版镜像。
- 备份：定期打包 `./data`（Chroma 目录 + SQLite 文件）。
- 日志：容器内为 JSON 结构化日志（`APP_LOG_LEVEL` 控制级别）。
- 最小权限：容器内以非 root 运行更安全，可在 Dockerfile 中追加 `useradd` 步骤（当前镜像为默认用户）。

## 6. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| `numpy` 源码编译失败 | Python 3.13 + 旧 numpy 无轮子 | 使用 `requirements.lock`（numpy≥2.1）；Windows 建议 `--only-binary=:all:` |
| 端口占用 | 8000 已被占 | 改 `APP_PORT` 或 compose 端口映射 |
| `/health` 返回但 chat 慢 | 真实模型首次加载 | 预热一次请求；或先用 `mock` 验证链路 |
| Chroma 目录锁死 | 同目录被多进程打开 | 确保单实例访问 `APP_CHROMA_PATH` |
| `docker build` 报 `failed to fetch anonymous token` | 本机访问 Docker Hub 被网络/代理阻断 | 见下方 6.1 |

### 6.1 Docker Hub 不可达时的构建办法（本机实测有效）

现象：`failed to authorize: failed to fetch anonymous token ... Bad Gateway`。
诊断顺序：宿主机直连/代理访问 `https://auth.docker.io/token` → 若均失败，说明是网络侧限制，不是 Dockerfile 问题。

绕行（无需改动 Dockerfile、无需重启 Docker Desktop）：

```bash
# 1) 从可用加速器域名直接拉基础镜像
docker pull docker.m.daocloud.io/library/python:3.13-slim
# 2) 打成本地 tag，让 FROM python:3.13-slim 命中缓存
docker tag docker.m.daocloud.io/library/python:3.13-slim python:3.13-slim
# 3) 正常构建
docker build -t ai-platform-agent-rag:0.1.0 .
```

长效方案：Docker Desktop → Settings → Docker Engine，加入
`"registry-mirrors": ["https://docker.m.daocloud.io"]` 后重启 Docker Desktop。
注意：重启 Docker 会停止所有容器，重启策略为 `no` 的容器（如 Pi Node testnet2）不会自动恢复，需手动 `docker start`。
