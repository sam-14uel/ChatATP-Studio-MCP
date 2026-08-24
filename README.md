# ChatATP Studio MCP Server

Remote FastMCP server that turns the Studio Django `/dapi/` API into MCP tools.

Public URL this project is built for:

```
https://mcp.chat-atp.com/studio/mcp
```

Clients (Cursor, Claude, Copilot, ChatATP agents) connect there over **Streamable HTTP**. Every tool call is proxied to your existing backend with the caller's `Authorization` header.

## What you get

Action-oriented tools over:

- Agents (`list_agents`, `create_agent`, `preview_agent`, ...)
- Knowledge bases + agent attachments
- MCP server definitions + connections
- HTTP API tools + `execute_http_api_connection`
- LLM providers + API-key configs
- Messaging platforms
- Teams / whoami

Deletes and disconnects require `confirm=true`.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export STUDIO_API_URL=https://chatatp-agent-builder-backend.onrender.com
export STUDIO_TOKEN=chatatp_sk_...   # optional fallback
uvicorn app:app --host 0.0.0.0 --port 8000
```

Check:

```bash
curl http://localhost:8000/health
```

MCP endpoint:

```
http://localhost:8000/studio/mcp
```

## Auth

1. Preferred: the MCP client sends  
   `Authorization: Bearer <studio jwt or chatatp_sk_...>`  
   The server forwards that header to `/dapi/`.
2. Fallback: `STUDIO_TOKEN` / `STUDIO_API_KEY` in the environment (single-tenant / internal).

Do not bake customer tokens into the image.

## Deploy at mcp.chat-atp.com/studio/mcp

Point the `mcp.chat-atp.com` host at this service **with the path intact**.  
`MCP_PATH` defaults to `/studio/mcp`, so the process should own the hostname (or receive `/studio/mcp` unstripped).

### Docker

```bash
docker build -t chatatp-studio-mcp .
docker run --rm -p 8000:8000 \
  -e STUDIO_API_URL=https://chatatp-agent-builder-backend.onrender.com \
  -e STUDIO_TOKEN=... \
  chatatp-studio-mcp
```

### Render

This repo includes `render.yaml`. After deploy, put Cloudflare / DNS:

```
mcp.chat-atp.com  →  <your-render-service>.onrender.com
```

If you already have something else on `mcp.chat-atp.com` and only want `/studio/*` here, reverse-proxy without stripping the prefix:

```nginx
location /studio/ {
    proxy_pass http://studio-mcp:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header Authorization $http_authorization;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_buffering off;
    proxy_read_timeout 120s;
}

location /health {
    proxy_pass http://studio-mcp:8000/health;
}
```

Caddy:

```
mcp.chat-atp.com {
    reverse_proxy /studio/* localhost:8000
    reverse_proxy /health localhost:8000
}
```

If your proxy **strips** `/studio`, set `MCP_PATH=/mcp` so the public URL is still `/studio/mcp` after the strip. Do not do both.

## Connect a client

Cursor / Claude Desktop / any Streamable HTTP MCP client:

```json
{
  "mcpServers": {
    "chatatp-studio": {
      "url": "https://mcp.chat-atp.com/studio/mcp",
      "headers": {
        "Authorization": "Bearer chatatp_sk_..."
      }
    }
  }
}
```

Inspector:

```bash
npx @modelcontextprotocol/inspector
# then connect to http://localhost:8000/studio/mcp
```

## Env

| Variable | Default | Purpose |
|---|---|---|
| `STUDIO_API_URL` | Render backend URL | Django base URL |
| `STUDIO_TOKEN` | empty | Fallback auth |
| `MCP_PATH` | `/studio/mcp` | Public MCP path |
| `PORT` | `8000` | Listen port |
| `STUDIO_TIMEOUT` | `30` | Upstream timeout seconds |
| `MCP_STATELESS` | `true` | Stateless Streamable HTTP (good behind load balancers) |

## Notes

- Paths marked inferred in the Studio CLI (`/dapi/mcp/servers/`, `/dapi/http-api/tools/`, `/dapi/llm/configs/`, agent preview) live in `studio_mcp/endpoints.py`. If a route 404s, change only that file.
- Document upload is not exposed yet (multipart). Add a dedicated tool when you want file ingest from MCP.
- Copilot assistant endpoints (`/dapi/assistant/...`) are intentionally not wrapped so this server does not recurse into Copilot.
