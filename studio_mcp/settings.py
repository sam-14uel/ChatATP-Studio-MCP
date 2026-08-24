"""Runtime config from environment."""

from __future__ import annotations

import os


DEFAULT_STUDIO_API_URL = "https://chatatp-agent-builder-backend.onrender.com"
DEFAULT_MCP_PATH = "/studio/mcp"


def env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    if value is None or value == "":
        return default
    return value


STUDIO_API_URL = (env("STUDIO_API_URL", DEFAULT_STUDIO_API_URL) or DEFAULT_STUDIO_API_URL).rstrip("/")
STUDIO_TOKEN = env("STUDIO_TOKEN") or env("STUDIO_API_KEY") or ""
MCP_PATH = env("MCP_PATH", DEFAULT_MCP_PATH) or DEFAULT_MCP_PATH
HOST = env("HOST", "0.0.0.0") or "0.0.0.0"
PORT = int(env("PORT", "8000") or "8000")
TIMEOUT = float(env("STUDIO_TIMEOUT", "30") or "30")
STATLESS = (env("MCP_STATELESS", "true") or "true").lower() in {"1", "true", "yes"}
