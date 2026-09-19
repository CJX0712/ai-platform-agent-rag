"""端到端冒烟脚本：对运行中的服务做核心成功流 + 关键错误流验证。

用法：
    python scripts/e2e_check.py                       # 默认 http://127.0.0.1:8000
    BASE_URL=http://43.161.233.163:8000 python scripts/e2e_check.py

退出码 0 = 全绿，1 = 存在失败项。
作者：晨星
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8000").rstrip("/")

_results: list[tuple[str, bool, str]] = []


def http(method: str, path: str, payload: dict | None = None, token: str | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw or "{}")
            except json.JSONDecodeError:
                return r.status, raw
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, bool(ok), detail))
    flag = "PASS" if ok else "FAIL"
    print(f"[{flag}] {name}" + (f" | {detail}" if detail else ""))


def wait_ready(timeout: int = 40) -> bool:
    for _ in range(timeout):
        try:
            s, _ = http("GET", "/health")
            if s == 200:
                return True
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1)
    return False


def main() -> int:
    print(f"目标服务: {BASE}\n")
    if not wait_ready():
        print("服务未就绪，终止")
        return 1

    s, b = http("GET", "/health")
    check("健康检查 /health", s == 200 and b.get("status") == "ok", f"status={s}")

    s, b = http("GET", "/v1/tools")
    names = {t["name"] for t in b} if isinstance(b, list) else set()
    check("工具清单 /v1/tools", s == 200 and "calculator" in names, f"tools={sorted(names)}")

    doc = "本项目用 LangGraph 做 Agent 编排，Chroma 做向量检索，FastAPI 提供网关。"
    s, b = http("POST", "/v1/ingest", {"text": doc, "title": "架构说明"})
    check("知识摄取 /v1/ingest", s == 200 and b.get("chunks", 0) >= 1, f"chunks={b.get('chunks')}")

    s, b = http("POST", "/v1/chat", {"message": "本项目用什么做向量检索？"})
    hit = isinstance(b, dict) and bool(b.get("context"))
    check("RAG 链路 /v1/chat", s == 200 and hit and bool(b.get("conv_id")),
          f"context_hit={hit}")

    s, b = http("POST", "/v1/chat", {"message": "计算 123*45+6"})
    tr = b.get("tool_result", "") if isinstance(b, dict) else ""
    check("工具链路 /v1/chat", s == 200 and "5541" in tr, f"tool_result={tr}")

    # 错误流：参数缺失
    s, _ = http("POST", "/v1/chat", {})
    check("错误流 参数缺失 返回 422", s == 422, f"status={s}")

    # WebSocket（可选失败不阻断，websockets 未安装时跳过）
    try:
        import asyncio

        import websockets

        async def ws_once():
            url = BASE.replace("http://", "ws://").replace("https://", "wss://") + "/ws/chat"
            async with websockets.connect(url, open_timeout=30) as ws:  # type: ignore[attr-defined]
                await ws.send(json.dumps({"message": "你好"}))
                return json.loads(await asyncio.wait_for(ws.recv(), timeout=60))

        data = asyncio.run(ws_once())
        check("WebSocket /ws/chat", "answer" in data, f"keys={sorted(data)}")
    except Exception as exc:  # noqa: BLE001
        check("WebSocket /ws/chat", False, f"跳过或失败: {exc}")

    failed = [n for n, ok, _ in _results if not ok]
    total = len(_results)
    print(f"\n结果: {total - len(failed)}/{total} 通过")
    if failed:
        print("失败项: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
