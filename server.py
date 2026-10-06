"""
Jira MCP Server - entry point.

Connects to a Jira Server/Data Center instance using a Personal Access Token
and exposes comprehensive Jira operations as MCP tools.

Environment variables (required):
    JIRA_URL: Jira base URL, e.g. https://jira.elevancehealth.com
    JIRA_PAT: Personal Access Token from Jira profile settings

Usage:
    python server.py                  # stdio transport (for Windsurf/Cascade)
    python server.py --transport sse  # SSE transport for HTTP-based clients
"""

import logging
import sys

# from mcp.server.mcpserver.server import MCPServer as FastMCP
from mcp.server import MCPServer as FastMCP

from tools.issues import register_issue_tools
from tools.projects import register_project_tools
from tools.search import register_search_tools
from tools.sprints import register_sprint_tools
from tools.users import register_user_tools

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "jira_mcp",
    instructions=(
        "You are connected to a Jira Server/Data Center instance. "
        "Use these tools to manage Jira issues, projects, sprints, and users. "
        "Always use jira_get_transitions before jira_transition_issue. "
        "Use jira_search_issues with JQL for flexible queries. "
        "Use jira_get_boards -> jira_get_sprints -> jira_get_sprint_issues for sprint work."
    ),
)

register_issue_tools(mcp)
register_search_tools(mcp)
register_project_tools(mcp)
register_sprint_tools(mcp)
register_user_tools(mcp)

logger.info("jira_mcp server initialized - %d tool modules loaded.", 5)


def main() -> None:
    """Start the Jira MCP server using stdio transport."""
    transport = "stdio"
    if len(sys.argv) > 2 and sys.argv[1] == "--transport":
        transport = sys.argv[2]
    logger.info("Starting jira_mcp server with transport=%s", transport)
    import asyncio

    if transport == "stdio":
        asyncio.run(mcp.run_stdio_async())
    elif transport == "sse":
        asyncio.run(mcp.run_sse_async())
    else:
        asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()