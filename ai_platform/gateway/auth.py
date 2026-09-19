"""鉴权模块：JWT 签发与校验（可关闭）。

单一职责：仅在开启 APP_AUTH_ENABLED 时强制鉴权；关闭时回退匿名用户，便于离线演示。
作者：晨星
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ai_platform.config import Settings, get_settings

_bearer = HTTPBearer(auto_error=False)


def create_token(settings: Settings, sub: str) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_min)
    return jwt.encode({"sub": sub, "exp": exp}, settings.jwt_secret, algorithm=settings.jwt_alg)


def verify_token(settings: Settings, token: str) -> str | None:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])["sub"]
    except JWTError:
        return None


def get_current_user(
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
) -> str:
    """鉴权依赖：关闭时返回 anonymous；开启时校验 Bearer。"""
    settings = get_settings()
    if not settings.auth_enabled:
        return "anonymous"
    if creds is None or not verify_token(settings, creds.credentials):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效或缺失令牌")
    return verify_token(settings, creds.credentials)
