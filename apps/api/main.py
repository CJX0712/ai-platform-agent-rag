"""服务入口：uvicorn 启动 FastAPI 应用。

用法：
    python -m apps.api.main
    uvicorn apps.api.main:app --host 0.0.0.0 --port 8000

作者：晨星
"""

from __future__ import annotations

import uvicorn

from ai_platform.config import get_settings
from ai_platform.gateway.app import create_app
from ai_platform.observability import configure_logging

app = create_app()


if __name__ == "__main__":
    configure_logging(get_settings().log_level)
    s = get_settings()
    uvicorn.run(app, host=s.host, port=s.port)
