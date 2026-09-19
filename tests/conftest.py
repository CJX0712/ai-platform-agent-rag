"""测试公共 fixtures：在导入任何 ai_platform 模块前固定 env，保证干净可复现。

作者：晨星
"""

import os
import tempfile

os.environ["APP_AUTH_ENABLED"] = "false"
os.environ["APP_LLM_PROVIDER"] = "mock"
os.environ["APP_EMBEDDING_PROVIDER"] = "hash"
os.environ["APP_CHROMA_PATH"] = tempfile.mkdtemp(prefix="chroma_")
os.environ["APP_DATABASE_URL"] = "sqlite:///" + tempfile.mkdtemp(prefix="db_") + "/test.db"
os.environ["APP_CHROMA_COLLECTION"] = "test"

from ai_platform.config import get_settings  # noqa: E402

get_settings.cache_clear()
