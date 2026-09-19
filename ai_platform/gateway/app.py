"""API 应用工厂：装配路由、鉴权、限流、CORS、WebSocket。

单一职责：HTTP 接入层，零业务逻辑；所有能力委托给 compose.Container。
作者：晨星
"""

import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from ai_platform import __version__
from ai_platform import tools as tools_mod
from ai_platform.compose import Container
from ai_platform.config import get_settings
from ai_platform.gateway import schemas
from ai_platform.gateway.auth import create_token, get_current_user

limiter = Limiter(key_func=get_remote_address)


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.container = Container(settings)
        yield

    app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    quota = f"{settings.rate_limit_per_min}/minute"

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "version": __version__,
            "auth_enabled": settings.auth_enabled,
            "llm_provider": settings.llm_provider,
        }

    @app.post("/v1/chat", response_model=schemas.ChatResponse)
    @limiter.limit(quota)
    async def chat(req: schemas.ChatRequest, request: Request, _user: str = Depends(get_current_user)):
        container: Container = request.app.state.container
        res = container.agent.run(req.message, req.conv_id)
        return schemas.ChatResponse(**res)

    @app.post("/v1/ingest", response_model=schemas.IngestResponse)
    @limiter.limit("30/minute")
    async def ingest(req: schemas.IngestRequest, request: Request, _user: str = Depends(get_current_user)):
        container: Container = request.app.state.container
        doc_id = req.doc_id or str(uuid.uuid4())
        chunks = container.rag.ingest_text(req.text, doc_id, req.title)
        return schemas.IngestResponse(doc_id=doc_id, chunks=chunks)

    @app.get("/v1/tools")
    async def list_tools(_user: str = Depends(get_current_user)):
        return tools_mod.list_tools()

    @app.post("/v1/auth/token", response_model=schemas.TokenResponse)
    async def token(req: schemas.TokenRequest):
        if not settings.auth_enabled:
            return JSONResponse(status_code=400, content={"detail": "鉴权未开启，设置 APP_AUTH_ENABLED=true 后可用"})
        if req.username != settings.demo_username or req.password != settings.demo_password:
            return JSONResponse(status_code=401, content={"detail": "用户名或密码错误"})
        return schemas.TokenResponse(access_token=create_token(settings, req.username))

    @app.websocket("/ws/chat")
    async def ws_chat(ws: WebSocket):
        await ws.accept()
        try:
            container: Container = ws.app.state.container
            while True:
                data = await ws.receive_json()
                res = container.agent.run(data.get("message", ""), data.get("conv_id"))
                await ws.send_json(res)
        except WebSocketDisconnect:
            return

    return app


def _rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:  # noqa: ARG001
    return JSONResponse(status_code=429, content={"detail": "请求过于频繁，请稍后再试"})
