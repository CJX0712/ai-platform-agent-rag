"""API 请求/响应数据模型。"""

from __future__ import annotations

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    conv_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    conv_id: str
    context: list[str] = []
    tool_result: str = ""


class IngestRequest(BaseModel):
    text: str
    doc_id: str | None = None
    title: str = ""


class IngestResponse(BaseModel):
    doc_id: str
    chunks: int


class TokenRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
