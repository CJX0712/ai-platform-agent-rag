"""工具集单测。"""

from ai_platform import tools as t


def test_calculator():
    assert t.call_tool("calculator", "2*3+4") == "10"


def test_registry():
    names = {x["name"] for x in t.list_tools()}
    assert {"calculator", "datetime", "search"} <= names


def test_unknown_tool():
    assert "未知工具" in t.call_tool("nope", "x")
