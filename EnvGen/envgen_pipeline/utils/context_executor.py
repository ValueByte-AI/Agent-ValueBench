"""ThreadPoolExecutor that preserves contextvars across worker threads."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context


class ContextThreadPoolExecutor(ThreadPoolExecutor):
    """Propagate the caller context into each submitted worker."""

    def submit(self, fn, /, *args, **kwargs):  # type: ignore[override]
        ctx = copy_context()
        return super().submit(ctx.run, fn, *args, **kwargs)
