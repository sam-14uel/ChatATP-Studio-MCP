"""ASGI entrypoint for uvicorn / Docker / Render.

Public MCP URL when this process owns mcp.chat-atp.com:

    https://mcp.chat-atp.com/studio/mcp

Health:

    https://mcp.chat-atp.com/health
"""

from studio_mcp.server import http_app

app = http_app()
