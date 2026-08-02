"""
LangChain integration (deprecated entry point).

Canonical handler lives at::

    from epi_recorder.adapters.langchain import EpiCallbackHandler

This module keeps ``EPICallbackHandler`` as a thin compatibility alias that
emits ``DeprecationWarning`` and delegates to the adapters implementation.
"""

from __future__ import annotations

import warnings
from typing import Any, Optional

from epi_recorder.adapters.langchain import EpiCallbackHandler as _CanonicalHandler


class _LazyCurrentSession:
    """Resolve the active ``record()`` session at log time (legacy no-arg ctor)."""

    def log(self, kind: str, content: dict | None = None, **kwargs: Any) -> None:
        from epi_recorder.api import get_current_session

        session = get_current_session()
        if session is None:
            return
        log_fn = getattr(session, "log", None) or getattr(session, "log_step", None)
        if log_fn is None:
            return
        if content is None:
            content = dict(kwargs)
        elif kwargs:
            merged = dict(content)
            merged.update(kwargs)
            content = merged
        log_fn(kind, content)

    def log_step(self, kind: str, content: dict | None = None, **kwargs: Any) -> None:
        self.log(kind, content, **kwargs)


class EPICallbackHandler(_CanonicalHandler):
    """
    Deprecated alias for ``epi_recorder.adapters.langchain.EpiCallbackHandler``.

    Prefer::

        with record("run.epi") as session:
            handler = EpiCallbackHandler(session)

    Legacy no-arg construction still works inside an active ``record()`` context
    (session resolved lazily via ``get_current_session()``).
    """

    name: str = "EPICallbackHandler"

    def __init__(self, session: Any = None) -> None:
        warnings.warn(
            "epi_recorder.integrations.langchain.EPICallbackHandler is deprecated; "
            "use epi_recorder.adapters.langchain.EpiCallbackHandler(session) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._explicit_session = session
        if session is None:
            session = _LazyCurrentSession()
        super().__init__(session)

    def _get_session(self) -> Any:
        """Legacy hook used by older tests/call sites."""
        if self._explicit_session is not None:
            return self._explicit_session
        try:
            from epi_recorder.api import get_current_session

            return get_current_session()
        except Exception:
            return None

    def _log(self, kind: str, content: dict) -> None:
        # Route through _get_session so monkeypatches keep working.
        session = self._get_session()
        if session is None:
            return
        log_fn = getattr(session, "log", None) or getattr(session, "log_step", None)
        if log_fn is None:
            return
        try:
            log_fn(kind, content)
        except Exception:
            if self.raise_error:
                raise


# Back-compat module flag used by some probes
try:
    from langchain_core.callbacks import BaseCallbackHandler  # noqa: F401

    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.callbacks.base import BaseCallbackHandler  # type: ignore # noqa: F401

        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False


__all__ = ["EPICallbackHandler", "LANGCHAIN_AVAILABLE"]
