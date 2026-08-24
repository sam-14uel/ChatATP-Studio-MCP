"""HTTP client that forwards the incoming MCP Authorization header to Studio."""

from __future__ import annotations

from typing import Any

import httpx

from . import settings

try:
    from fastmcp.server.dependencies import get_http_headers
except Exception:  # pragma: no cover
    def get_http_headers(*_args: Any, **_kwargs: Any) -> dict[str, str]:
        return {}


def _auth_header() -> str | None:
    headers = {}
    try:
        headers = {str(k).lower(): str(v) for k, v in (get_http_headers() or {}).items()}
    except Exception:
        headers = {}

    incoming = headers.get("authorization") or headers.get("x-studio-token")
    if incoming:
        if incoming.lower().startswith("bearer ") or incoming.lower().startswith("token "):
            return incoming
        return f"Bearer {incoming}"

    if settings.STUDIO_TOKEN:
        token = settings.STUDIO_TOKEN
        if token.lower().startswith("bearer ") or token.lower().startswith("token "):
            return token
        scheme = "Token" if not token.startswith("chatatp_sk_") and len(token) < 64 else "Bearer"
        if token.startswith("chatatp_sk_") or "." in token:
            scheme = "Bearer"
        return f"{scheme} {token}"
    return None


async def studio_request(
    method: str,
    path: str,
    *,
    json: Any = None,
    params: dict[str, Any] | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    auth = _auth_header()
    if not auth:
        return {
            "error": 401,
            "detail": "Missing Studio credentials. Pass Authorization: Bearer <token> on the MCP request, or set STUDIO_TOKEN.",
        }
    headers["Authorization"] = auth

    clean_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}
    url = f"{settings.STUDIO_API_URL}{path}"

    async with httpx.AsyncClient(timeout=settings.TIMEOUT) as client:
        try:
            response = await client.request(
                method.upper(),
                url,
                headers=headers,
                json=json,
                params=clean_params or None,
            )
        except httpx.TimeoutException:
            return {"error": 504, "detail": f"Studio API timed out calling {method} {path}"}
        except httpx.RequestError as exc:
            return {"error": 502, "detail": f"Studio API unreachable: {exc}"}

    if response.status_code == 204:
        return {"ok": True}

    try:
        payload = response.json()
    except Exception:
        payload = response.text or None

    if response.is_error:
        return {
            "error": response.status_code,
            "detail": payload,
            "path": path,
        }
    return payload
