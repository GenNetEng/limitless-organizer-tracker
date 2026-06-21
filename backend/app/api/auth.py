from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

import app.config

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _parse_keys() -> set[str]:
    return {k.strip() for k in app.config.settings.api_keys.split(",") if k.strip()}


async def require_api_key(key: str | None = Security(_api_key_header)) -> str | None:
    valid_keys = _parse_keys()
    if not valid_keys:
        return None
    if key is None or key not in valid_keys:
        raise HTTPException(status_code=401, detail="Missing or invalid API key")
    return key
