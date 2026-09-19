"""工具集模块：工具注册表 + 内置安全工具。

单一职责：为 Agent 提供可扩展的工具能力。新增工具只需实现 ToolSpec 并 register。
作者：晨星
"""

from __future__ import annotations

import ast
import operator
import re
import time
from typing import Protocol, runtime_checkable


@runtime_checkable
class ToolSpec(Protocol):
    """工具接口。"""

    name: str
    description: str

    def run(self, arg: str) -> str: ...


class CalculatorTool:
    """仅支持基础算术的安全计算器（AST 白名单，杜绝代码执行风险）。"""

    name = "calculator"
    description = "安全计算算术表达式，如 123 * 456"

    _OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    # 从自然语言中抽取算术片段，如 "计算 123*45+6 等于多少" -> "123*45+6"
    _EXPR_RE = re.compile(r"[0-9][0-9\.\s\+\-\*/\(\)%×÷\^]*")

    def run(self, arg: str) -> str:
        last_err = "未找到可计算的算术表达式"
        for expr in self._candidates(arg or ""):
            try:
                tree = ast.parse(expr, mode="eval")
                return str(self._eval(tree.body))
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
                continue
        return f"计算错误: {last_err}"

    def _candidates(self, text: str) -> list[str]:
        """候选表达式：整串优先，其次按长度降序的抽取片段。"""
        norm = text.replace("×", "*").replace("÷", "/").replace("^", "**")
        cands = [norm.strip()]
        for frag in self._EXPR_RE.findall(norm):
            frag = frag.strip()
            if re.search(r"\d", frag) and re.search(r"[+\-*/%]", frag):
                cands.append(frag)
        return [c for c in cands if c]

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.BinOp):
            return self._OPS[type(node.op)](self._eval(node.left), self._eval(node.right))
        if isinstance(node, ast.UnaryOp):
            return self._OPS[type(node.op)](self._eval(node.operand))
        raise ValueError("仅支持基础算术表达式")


class DateTimeTool:
    """返回当前时间。"""

    name = "datetime"
    description = "返回服务器当前时间"

    def run(self, arg: str) -> str:
        return time.strftime("%Y-%m-%d %H:%M:%S %Z")


class SearchTool:
    """联网搜索占位（演示返回，真实可接入搜索 API）。"""

    name = "search"
    description = "联网搜索（演示占位，可接入真实搜索服务）"

    def run(self, arg: str) -> str:
        return f"[search-demo] 未接入真实搜索服务，关键词：{arg[:80]}"


_REGISTRY: dict[str, ToolSpec] = {}


def register(tool: ToolSpec) -> ToolSpec:
    _REGISTRY[tool.name] = tool
    return tool


register(CalculatorTool())
register(DateTimeTool())
register(SearchTool())


def get_tool(name: str) -> ToolSpec | None:
    return _REGISTRY.get(name)


def list_tools() -> list[dict]:
    return [{"name": t.name, "description": t.description} for t in _REGISTRY.values()]


def call_tool(name: str, arg: str) -> str:
    tool = _REGISTRY.get(name)
    if tool is None:
        return f"未知工具: {name}"
    return tool.run(arg)
