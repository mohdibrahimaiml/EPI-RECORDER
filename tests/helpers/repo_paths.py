"""Resolve checkout-only files when tests run against an installed wheel."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def require_repo_file(*parts: str) -> Path:
    """Return a path under the git checkout, or skip if it is not on disk.

    Viewer/docs/portal samples are not packed in the wheel. Tests that assert
    those files must use this helper so a checkout run still works from any
    cwd, and an installed-wheel-only environment skips with a clear reason.
    """
    path = REPO_ROOT.joinpath(*parts)
    if not path.exists():
        rel = "/".join(parts)
        pytest.skip(
            f"{rel} is not in the installed wheel; checkout-only asset"
        )
    return path
