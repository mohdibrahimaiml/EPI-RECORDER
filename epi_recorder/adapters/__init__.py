"""
Optional framework adapters for epi-recorder.

Import submodules explicitly, e.g.::

    from epi_recorder.adapters.langchain import EpiCallbackHandler

These packages require optional dependencies (see ``pip install epi-recorder[langchain]``).
Importing ``epi_recorder`` alone never loads adapter deps.
"""

from __future__ import annotations

__all__ = ["langchain"]
