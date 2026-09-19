"""Agent 编排模块：基于 LangGraph 的状态图。

单一职责：把 Planner / Retrieve / Tool / Answer 编排成可回溯、可观测的决策流，
组合 rag + tools + llm + memory 四大能力，对外暴露 AgentEngine.run。
作者：晨星
"""

from __future__ import annotations

import json
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from ai_platform import tools as tools_mod
from ai_platform.config import Settings
from ai_platform.llm import LLMClient
from ai_platform.memory import MemoryStore
from ai_platform.rag import RagService


class AgentState(TypedDict, total=False):
    """编排状态。"""

    query: str
    conv_id: str
    context: list
    tool_result: str
    answer: str
    _decision: str
    _tool: str
    _arg: str


_SYSTEM_PROMPT = (
    "你是一个严谨的 AI 助手。若提供了 <context> 检索到的资料，请优先基于资料作答并注明来源；"
    "若提供了 <tool_result> 工具结果，请据此总结。若无相关资料，诚实说明。"
)


class AgentEngine:
    """基于 LangGraph 的 Agent 运行时。"""

    def __init__(
        self,
        settings: Settings,
        llm: LLMClient,
        rag: RagService,
        memory: MemoryStore,
        tools_module=tools_mod,
    ) -> None:
        self.settings = settings
        self.llm = llm
        self.rag = rag
        self.memory = memory
        self.tools = tools_module
        self.graph = self._build()

    def _build(self):
        g = StateGraph(AgentState)
        g.add_node("plan", self._plan)
        g.add_edge(START, "plan")
        g.add_node("retrieve", self._retrieve)
        g.add_node("tool", self._tool)
        # 节点名不可与 AgentState 的键同名（langgraph 会视为重复 state key）
        g.add_node("respond", self._answer)
        g.add_conditional_edges(
            "plan",
            self._route,
            {"retrieve": "retrieve", "tool": "tool", "answer": "respond"},
        )
        g.add_edge("retrieve", "respond")
        g.add_edge("tool", "respond")
        g.add_edge("respond", END)
        return g.compile()

    # ---- 节点 ----

    def _plan(self, state: AgentState) -> dict:
        if self.settings.llm_provider.lower() == "mock":
            q = state["query"].lower()
            calc_keys = ("计算", "calc", "calculate", "+", "-", "*", "/", "%", "×", "÷")
            if re.search(r"[\d]", q) and any(k in q for k in calc_keys):
                return {"_decision": "tool", "_tool": "calculator", "_arg": state["query"]}
            # 离线演示默认走检索，验证 RAG 链路
            return {"_decision": "retrieve"}
        return self._llm_decide(state)

    def _llm_decide(self, state: AgentState) -> dict:
        prompt = (
            "请判断下一步动作，仅输出 JSON："
            '{"action":"retrieve"|"tool"|"answer","tool":<工具名>,"arg":<参数>}\n'
            "可用工具：" + ", ".join(t["name"] for t in self.tools.list_tools())
        )
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": state["query"]},
        ]
        raw = self.llm.chat(messages)
        try:
            data = json.loads(raw)
            action = data.get("action", "answer")
            return {
                "_decision": action,
                "_tool": data.get("tool", ""),
                "_arg": data.get("arg", state["query"]),
            }
        except Exception:  # noqa: BLE001
            return {"_decision": "answer"}

    def _retrieve(self, state: AgentState) -> dict:
        ctx = self.rag.retrieve(state["query"], k=4)
        return {"context": ctx, "_decision": "answer"}

    def _tool(self, state: AgentState) -> dict:
        name = state.get("_tool", "calculator")
        arg = state.get("_arg", state["query"])
        result = self.tools.call_tool(name, arg)
        return {"tool_result": result, "_decision": "answer"}

    def _answer(self, state: AgentState) -> dict:
        messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
        if state.get("context"):
            ctx_text = "\n".join(f"- {c}" for c in state["context"])
            messages.append({"role": "system", "content": f"<context>\n{ctx_text}\n</context>"})
        if state.get("tool_result"):
            messages.append({"role": "system", "content": f"<tool_result>\n{state['tool_result']}\n</tool_result>"})
        for m in self.memory.history(state["conv_id"]):
            messages.append(m)
        messages.append({"role": "user", "content": state["query"]})
        answer = self.llm.chat(messages)
        return {"answer": answer}

    def _route(self, state: AgentState) -> str:
        return state.get("_decision", "answer")

    # ---- 对外接口 ----

    def run(self, user_input: str, conv_id: str | None = None) -> dict:
        """执行一轮对话，返回答案、会话 id、检索上下文与工具结果。"""
        if not conv_id:
            conv_id = self.memory.new_conversation()
        self.memory.ensure(conv_id)
        self.memory.add(conv_id, "user", user_input)
        init: AgentState = {
            "query": user_input,
            "conv_id": conv_id,
            "context": [],
            "tool_result": "",
            "answer": "",
        }
        result = self.graph.invoke(init)
        answer = result.get("answer", "")
        self.memory.add(conv_id, "assistant", answer)
        return {
            "answer": answer,
            "conv_id": conv_id,
            "context": result.get("context", []),
            "tool_result": result.get("tool_result", ""),
        }
