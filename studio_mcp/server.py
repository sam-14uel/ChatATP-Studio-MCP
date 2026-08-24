"""FastMCP server wrapping the ChatATP Studio Django /dapi/ API."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from . import endpoints as ep
from . import settings
from .client import studio_request

mcp = FastMCP(
    "ChatATP Studio",
    instructions=(
        "Manage ChatATP Studio agents, tools, knowledge bases, LLM configs, "
        "and messaging platforms through the Studio dashboard API. "
        "Prefer list/get before update/delete. Destructive tools require confirm=true."
    ),
    stateless_http=settings.STATLESS,
)


@mcp.custom_route("/health", methods=["GET"])
async def health(_request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "service": "chatatp-studio-mcp",
            "studio_api": settings.STUDIO_API_URL,
            "mcp_path": settings.MCP_PATH,
        }
    )


def _drop_none(payload: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in payload.items() if v is not None}


# ---------------------------------------------------------------------------
# Account
# ---------------------------------------------------------------------------


@mcp.tool
async def whoami() -> Any:
    """Return the authenticated Studio user (GET /dapi/auth/me/)."""
    return await studio_request("GET", ep.AUTH_ME)


@mcp.tool
async def update_profile(name: str | None = None, avatar_url: str | None = None) -> Any:
    """Update the current user's profile."""
    return await studio_request("PATCH", ep.AUTH_PROFILE, json=_drop_none({"name": name, "avatar_url": avatar_url}))


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


@mcp.tool
async def list_agents(query: str | None = None, page: int = 1, page_size: int = 20) -> Any:
    """List Studio agents. Optional search query filters by name/description."""
    return await studio_request(
        "GET",
        ep.AGENTS,
        params={"search": query, "page": page, "page_size": page_size},
    )


@mcp.tool
async def get_agent(agent_id: int) -> Any:
    """Get one agent by id, including attached tools, KBs, and LLM config."""
    return await studio_request("GET", ep.AGENT_DETAIL.format(id=agent_id))


@mcp.tool
async def create_agent(
    name: str,
    system_prompt: str,
    model_name: str | None = None,
    description: str | None = None,
    tone: str | None = None,
    llm_provider_config: int | None = None,
    status: str | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    """Create a Studio agent. Returns the created agent including its id."""
    body = _drop_none(
        {
            "name": name,
            "system_prompt": system_prompt,
            "model_name": model_name,
            "description": description,
            "tone": tone,
            "llm_provider_config": llm_provider_config,
            "status": status,
        }
    )
    if extra:
        body.update(extra)
    return await studio_request("POST", ep.AGENTS, json=body)


@mcp.tool
async def update_agent(agent_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an agent. Pass only fields to change (name, system_prompt, tool_connections, platform_configs, status, ...)."""
    return await studio_request("PATCH", ep.AGENT_DETAIL.format(id=agent_id), json=fields)


@mcp.tool
async def delete_agent(agent_id: int, confirm: bool = False) -> Any:
    """Permanently delete an agent. Must pass confirm=true."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this agent."}
    return await studio_request("DELETE", ep.AGENT_DETAIL.format(id=agent_id))


@mcp.tool
async def preview_agent(agent_id: int, message: str) -> Any:
    """Send a one-off test message to an agent and return the reply plus any tool calls."""
    return await studio_request("POST", ep.AGENT_PREVIEW.format(id=agent_id), json={"message": message})


# ---------------------------------------------------------------------------
# Knowledge bases
# ---------------------------------------------------------------------------


@mcp.tool
async def list_knowledge_bases(page: int = 1, page_size: int = 20) -> Any:
    """List standalone knowledge bases."""
    return await studio_request("GET", ep.KB_LIST, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_knowledge_base(kb_id: int) -> Any:
    """Get a standalone knowledge base by id."""
    return await studio_request("GET", ep.KB_DETAIL.format(id=kb_id))


@mcp.tool
async def create_knowledge_base(name: str, description: str | None = None) -> Any:
    """Create a standalone knowledge base."""
    return await studio_request("POST", ep.KB_LIST, json=_drop_none({"name": name, "description": description}))


@mcp.tool
async def update_knowledge_base(kb_id: int, fields: dict[str, Any]) -> Any:
    """Partially update a knowledge base."""
    return await studio_request("PATCH", ep.KB_DETAIL.format(id=kb_id), json=fields)


@mcp.tool
async def delete_knowledge_base(kb_id: int, confirm: bool = False) -> Any:
    """Delete a standalone knowledge base. Must pass confirm=true."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this knowledge base."}
    return await studio_request("DELETE", ep.KB_DETAIL.format(id=kb_id))


@mcp.tool
async def list_kb_documents(kb_id: int) -> Any:
    """List documents in a standalone knowledge base."""
    return await studio_request("GET", ep.KB_DOCUMENTS.format(id=kb_id))


@mcp.tool
async def delete_kb_document(kb_id: int, doc_id: int, confirm: bool = False) -> Any:
    """Delete a document from a standalone knowledge base."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this document."}
    return await studio_request("DELETE", ep.KB_DOCUMENT_DETAIL.format(id=kb_id, doc_id=doc_id))


@mcp.tool
async def add_kb_domain(kb_id: int, domain: str) -> Any:
    """Add a crawl domain to a standalone knowledge base."""
    return await studio_request("POST", ep.KB_DOMAINS.format(id=kb_id), json={"domain": domain})


@mcp.tool
async def crawl_kb_domain(kb_id: int, domain_id: int) -> Any:
    """Start a crawl for a knowledge-base domain."""
    return await studio_request("POST", ep.KB_DOMAIN_CRAWL.format(id=kb_id, domain_id=domain_id))


@mcp.tool
async def kb_stats(kb_id: int) -> Any:
    """Return indexing/document stats for a knowledge base."""
    return await studio_request("GET", ep.KB_STATS.format(id=kb_id))


@mcp.tool
async def search_knowledge_base(kb_id: int, query: str, top_k: int = 5) -> Any:
    """Search a standalone knowledge base and return the most relevant chunks."""
    return await studio_request("POST", ep.KB_SEARCH.format(id=kb_id), json={"query": query, "top_k": top_k})


@mcp.tool
async def list_agent_kb_attachments(agent_id: int) -> Any:
    """List knowledge bases attached to an agent."""
    return await studio_request("GET", ep.AGENT_KB_ATTACHMENTS.format(agent_id=agent_id))


@mcp.tool
async def list_available_kbs_for_agent(agent_id: int) -> Any:
    """List standalone knowledge bases that can still be attached to this agent."""
    return await studio_request("GET", ep.AGENT_KB_AVAILABLE.format(agent_id=agent_id))


@mcp.tool
async def attach_kb_to_agent(
    agent_id: int,
    knowledge_base_id: int,
    max_context_chunks: int | None = None,
) -> Any:
    """Attach an existing standalone knowledge base to an agent."""
    return await studio_request(
        "POST",
        ep.AGENT_KB_ATTACHMENTS.format(agent_id=agent_id),
        json=_drop_none({"knowledge_base_id": knowledge_base_id, "max_context_chunks": max_context_chunks}),
    )


@mcp.tool
async def detach_kb_from_agent(agent_id: int, attachment_id: int, confirm: bool = False) -> Any:
    """Detach a knowledge base from an agent."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to detach this knowledge base."}
    return await studio_request(
        "DELETE",
        ep.AGENT_KB_ATTACHMENT_DETAIL.format(agent_id=agent_id, attachment_id=attachment_id),
    )


@mcp.tool
async def search_agent_knowledge(agent_id: int, query: str, top_k: int = 5) -> Any:
    """Search knowledge attached to an agent."""
    return await studio_request(
        "POST",
        ep.AGENT_KB_SEARCH.format(agent_id=agent_id),
        json={"query": query, "top_k": top_k},
    )


@mcp.tool
async def test_agent_knowledge(agent_id: int, test_query: str) -> Any:
    """Run a retrieval test query against an agent's knowledge base."""
    return await studio_request(
        "POST",
        ep.AGENT_KB_TEST.format(agent_id=agent_id),
        json={"test_query": test_query},
    )


# ---------------------------------------------------------------------------
# MCP servers & connections (Studio's stored MCP definitions)
# ---------------------------------------------------------------------------


@mcp.tool
async def list_mcp_servers(page: int = 1, page_size: int = 20) -> Any:
    """List MCP server definitions stored in Studio."""
    return await studio_request("GET", ep.MCP_SERVERS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_mcp_server(server_id: int) -> Any:
    """Get one MCP server definition."""
    return await studio_request("GET", ep.MCP_SERVER_DETAIL.format(id=server_id))


@mcp.tool
async def create_mcp_server(fields: dict[str, Any]) -> Any:
    """Create an MCP server definition. Pass the serializer fields (name, url, transport, ...)."""
    return await studio_request("POST", ep.MCP_SERVERS, json=fields)


@mcp.tool
async def update_mcp_server(server_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an MCP server definition."""
    return await studio_request("PATCH", ep.MCP_SERVER_DETAIL.format(id=server_id), json=fields)


@mcp.tool
async def delete_mcp_server(server_id: int, confirm: bool = False) -> Any:
    """Delete an MCP server definition."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this MCP server."}
    return await studio_request("DELETE", ep.MCP_SERVER_DETAIL.format(id=server_id))


@mcp.tool
async def list_mcp_connections(page: int = 1, page_size: int = 20) -> Any:
    """List MCP connections (per-user/team credentials to a server)."""
    return await studio_request("GET", ep.MCP_CONNECTIONS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_mcp_connection(connection_id: int) -> Any:
    """Get one MCP connection."""
    return await studio_request("GET", ep.MCP_CONNECTION_DETAIL.format(id=connection_id))


@mcp.tool
async def create_mcp_connection(fields: dict[str, Any]) -> Any:
    """Create an MCP connection. Typical fields: server, label, credentials."""
    return await studio_request("POST", ep.MCP_CONNECTIONS, json=fields)


@mcp.tool
async def update_mcp_connection(connection_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an MCP connection."""
    return await studio_request("PATCH", ep.MCP_CONNECTION_DETAIL.format(id=connection_id), json=fields)


@mcp.tool
async def delete_mcp_connection(connection_id: int, confirm: bool = False) -> Any:
    """Delete an MCP connection."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this MCP connection."}
    return await studio_request("DELETE", ep.MCP_CONNECTION_DETAIL.format(id=connection_id))


@mcp.tool
async def initiate_mcp_oauth(connection_id: int) -> Any:
    """Start the OAuth flow for an MCP connection. Returns an authorization URL."""
    return await studio_request("POST", ep.MCP_OAUTH_INITIATE.format(id=connection_id))


# ---------------------------------------------------------------------------
# HTTP API tools
# ---------------------------------------------------------------------------


@mcp.tool
async def list_http_api_tools(page: int = 1, page_size: int = 20) -> Any:
    """List HTTP API tool definitions."""
    return await studio_request("GET", ep.HTTP_API_TOOLS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_http_api_tool(tool_id: int) -> Any:
    """Get one HTTP API tool definition."""
    return await studio_request("GET", ep.HTTP_API_TOOL_DETAIL.format(id=tool_id))


@mcp.tool
async def create_http_api_tool(fields: dict[str, Any]) -> Any:
    """Create an HTTP API tool definition."""
    return await studio_request("POST", ep.HTTP_API_TOOLS, json=fields)


@mcp.tool
async def update_http_api_tool(tool_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an HTTP API tool definition."""
    return await studio_request("PATCH", ep.HTTP_API_TOOL_DETAIL.format(id=tool_id), json=fields)


@mcp.tool
async def delete_http_api_tool(tool_id: int, confirm: bool = False) -> Any:
    """Delete an HTTP API tool definition."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this HTTP API tool."}
    return await studio_request("DELETE", ep.HTTP_API_TOOL_DETAIL.format(id=tool_id))


@mcp.tool
async def list_http_api_connections(page: int = 1, page_size: int = 20) -> Any:
    """List HTTP API connections."""
    return await studio_request("GET", ep.HTTP_API_CONNECTIONS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_http_api_connection(connection_id: int) -> Any:
    """Get one HTTP API connection."""
    return await studio_request("GET", ep.HTTP_API_CONNECTION_DETAIL.format(id=connection_id))


@mcp.tool
async def create_http_api_connection(fields: dict[str, Any]) -> Any:
    """Create an HTTP API connection."""
    return await studio_request("POST", ep.HTTP_API_CONNECTIONS, json=fields)


@mcp.tool
async def update_http_api_connection(connection_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an HTTP API connection."""
    return await studio_request("PATCH", ep.HTTP_API_CONNECTION_DETAIL.format(id=connection_id), json=fields)


@mcp.tool
async def delete_http_api_connection(connection_id: int, confirm: bool = False) -> Any:
    """Delete an HTTP API connection."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this HTTP API connection."}
    return await studio_request("DELETE", ep.HTTP_API_CONNECTION_DETAIL.format(id=connection_id))


@mcp.tool
async def execute_http_api_connection(connection_id: int, payload: dict[str, Any] | None = None) -> Any:
    """Execute an HTTP API connection with an optional JSON payload."""
    return await studio_request(
        "POST",
        ep.HTTP_API_CONNECTION_EXECUTE.format(id=connection_id),
        json=payload or {},
    )


@mcp.tool
async def initiate_http_api_oauth(connection_id: int) -> Any:
    """Start OAuth for an HTTP API connection."""
    return await studio_request("POST", ep.HTTP_API_OAUTH_INITIATE.format(id=connection_id))


# ---------------------------------------------------------------------------
# LLM providers
# ---------------------------------------------------------------------------


@mcp.tool
async def list_llm_providers() -> Any:
    """List the LLM provider catalog (OpenAI, Anthropic, ...)."""
    return await studio_request("GET", ep.LLM_PROVIDERS)


@mcp.tool
async def get_llm_provider(provider_id: int) -> Any:
    """Get one LLM provider from the catalog."""
    return await studio_request("GET", ep.LLM_PROVIDER_DETAIL.format(id=provider_id))


@mcp.tool
async def list_llm_models(provider_id: int) -> Any:
    """List models available for an LLM provider."""
    return await studio_request("GET", ep.LLM_PROVIDER_MODELS.format(id=provider_id))


@mcp.tool
async def list_llm_configs(page: int = 1, page_size: int = 20) -> Any:
    """List your stored LLM provider API-key configurations."""
    return await studio_request("GET", ep.LLM_PROVIDER_CONFIGS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_llm_config(config_id: int) -> Any:
    """Get one LLM provider configuration."""
    return await studio_request("GET", ep.LLM_PROVIDER_CONFIG_DETAIL.format(id=config_id))


@mcp.tool
async def create_llm_config(fields: dict[str, Any]) -> Any:
    """Create an LLM provider API-key configuration. Typical fields: provider, label, api_key."""
    return await studio_request("POST", ep.LLM_PROVIDER_CONFIGS, json=fields)


@mcp.tool
async def update_llm_config(config_id: int, fields: dict[str, Any]) -> Any:
    """Partially update an LLM provider configuration."""
    return await studio_request("PATCH", ep.LLM_PROVIDER_CONFIG_DETAIL.format(id=config_id), json=fields)


@mcp.tool
async def delete_llm_config(config_id: int, confirm: bool = False) -> Any:
    """Delete an LLM provider configuration."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this LLM config."}
    return await studio_request("DELETE", ep.LLM_PROVIDER_CONFIG_DETAIL.format(id=config_id))


# ---------------------------------------------------------------------------
# Platforms
# ---------------------------------------------------------------------------


@mcp.tool
async def list_platform_catalog() -> Any:
    """List messaging platforms (Discord, Slack, WhatsApp, ...)."""
    return await studio_request("GET", ep.PLATFORM_CATALOG)


@mcp.tool
async def get_platform_catalog_entry(platform_id: int) -> Any:
    """Get one platform catalog entry."""
    return await studio_request("GET", ep.PLATFORM_CATALOG_DETAIL.format(id=platform_id))


@mcp.tool
async def list_platform_configs(page: int = 1, page_size: int = 20) -> Any:
    """List connected platform configs."""
    return await studio_request("GET", ep.PLATFORM_CONFIGS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_platform_config(config_id: int) -> Any:
    """Get one platform config."""
    return await studio_request("GET", ep.PLATFORM_CONFIG_DETAIL.format(id=config_id))


@mcp.tool
async def create_platform_config(fields: dict[str, Any]) -> Any:
    """Create a platform config."""
    return await studio_request("POST", ep.PLATFORM_CONFIGS, json=fields)


@mcp.tool
async def update_platform_config(config_id: int, fields: dict[str, Any]) -> Any:
    """Partially update a platform config."""
    return await studio_request("PATCH", ep.PLATFORM_CONFIG_DETAIL.format(id=config_id), json=fields)


@mcp.tool
async def delete_platform_config(config_id: int, confirm: bool = False) -> Any:
    """Delete a platform config."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to delete this platform config."}
    return await studio_request("DELETE", ep.PLATFORM_CONFIG_DETAIL.format(id=config_id))


@mcp.tool
async def connect_platform(platform: int, credentials: dict[str, Any]) -> Any:
    """Connect a messaging platform with credentials (e.g. bot_token)."""
    return await studio_request("POST", ep.PLATFORM_CONNECT, json={"platform": platform, "credentials": credentials})


@mcp.tool
async def disconnect_platform(platform: int, confirm: bool = False) -> Any:
    """Disconnect a messaging platform."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to disconnect this platform."}
    return await studio_request("POST", ep.PLATFORM_DISCONNECT, json={"platform": platform})


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@mcp.tool
async def list_teams(page: int = 1, page_size: int = 20) -> Any:
    """List teams/workspaces."""
    return await studio_request("GET", ep.TEAMS, params={"page": page, "page_size": page_size})


@mcp.tool
async def get_team(team_id: int) -> Any:
    """Get one team."""
    return await studio_request("GET", ep.TEAM_DETAIL.format(id=team_id))


@mcp.tool
async def create_team(fields: dict[str, Any]) -> Any:
    """Create a team. Typical fields: name, slug."""
    return await studio_request("POST", ep.TEAMS, json=fields)


@mcp.tool
async def update_team(team_id: int, fields: dict[str, Any]) -> Any:
    """Partially update a team."""
    return await studio_request("PATCH", ep.TEAM_DETAIL.format(id=team_id), json=fields)


@mcp.tool
async def list_team_members(team_id: int) -> Any:
    """List members of a team."""
    return await studio_request("GET", ep.TEAM_MEMBERS.format(id=team_id))


@mcp.tool
async def add_team_member(team_id: int, user: int, role: str = "member") -> Any:
    """Add a user to a team."""
    return await studio_request("POST", ep.TEAM_MEMBERS.format(id=team_id), json={"user": user, "role": role})


@mcp.tool
async def remove_team_member(team_id: int, user_id: int, confirm: bool = False) -> Any:
    """Remove a user from a team."""
    if not confirm:
        return {"error": 400, "detail": "Pass confirm=true to remove this member."}
    return await studio_request("DELETE", ep.TEAM_MEMBER_DETAIL.format(id=team_id, user_id=user_id))


@mcp.tool
async def invite_team_member(team_id: int, email: str, role: str = "member") -> Any:
    """Invite someone to a team by email."""
    return await studio_request(
        "POST",
        ep.TEAM_INVITATIONS.format(id=team_id),
        json={"email": email, "role": role},
    )


def http_app():
    """ASGI app mounted so clients hit {origin}{MCP_PATH}."""
    return mcp.http_app(path=settings.MCP_PATH, stateless_http=settings.STATLESS)
