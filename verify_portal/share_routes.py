"""Share link routes historically lived here.

Canonical handlers are on `verify_portal.main` (`/api/share`, `/api/share/{id}`,
`/api/share/{id}/meta`). This module keeps an empty router so older imports of
`share_router` still resolve without registering duplicate OpenAPI paths.
"""

from fastapi import APIRouter

router = APIRouter()
