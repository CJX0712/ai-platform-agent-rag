"""可观测模块：结构化日志 + 轻量 trace/metrics 占位。

单一职责：为全链路提供统一日志与可观测接入点。生产可替换为 OpenTelemetry。
作者：晨星
"""

from __future__ import annotations

import logging

import structlog


def configure_logging(level: str = "INFO") -> None:
    """配置 structlog（JSON 输出，便于采集）。"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """获取带模块名的 logger。"""
    return structlog.get_logger(name)


class _Span:
    def __init__(self, name: str) -> None:
        self.name = name

    def __enter__(self) -> _Span:
        get_logger("trace").info("span.start", name=self.name)
        return self

    def __exit__(self, *exc: object) -> None:
        get_logger("trace").info("span.end", name=self.name)


class Tracer:
    """极简 tracer 占位，接口稳定，生产可替换为 OTel。"""

    @staticmethod
    def span(name: str) -> _Span:
        return _Span(name)


tracer = Tracer()
