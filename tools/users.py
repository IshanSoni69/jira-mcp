import json
import logging

# from mcp.server.mcpserver.server import MCPServer as FastMCP
from mcp.server import MCPServer as FastMCP

from jira_client import jira_get
from models import SearchUsersInput

logger = logging.getLogger(__name__)


def register_user_tools(mcp: FastMCP) -> None:
    """Register user-related tools on the MCP server instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(
        name="jira_get_current_user",
        annotations={
            "title": "Get Current Jira User",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_current_user() -> str:
        """Get profile information for the currently authenticated Jira user.

        Returns username, display name, email, account status, and timezone.

        Returns:
            JSON string with current user's profile details.
        """
        data = await jira_get("/myself")
        return json.dumps(
            {
                "username": data.get("name"),
                "account_id": data.get("accountId"),
                "display_name": data.get("displayName"),
                "email": data.get("emailAddress"),
                "active": data.get("active"),
                "timezone": data.get("timeZone"),
                "locale": data.get("locale"),
                "groups": [
                    g.get("name")
                    for g in (data.get("groups", {}).get("items") or [])
                ],
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_search_users",
        annotations={
            "title": "Search Jira Users",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_search_users(params: SearchUsersInput) -> str:
        """Search for Jira users by name, username, or email fragment.

        Useful for looking up usernames before assigning issues or adding watchers.
        Returns display name, username, email, and active status.

        Args:
            params: SearchUsersInput with query string and max_results.

        Returns:
            JSON string listing matching users.
        """
        data = await jira_get(
            "/user/search",
            params={
                "query": params.query,
                "maxResults": params.max_results,
                "includeActive": True,
                "includeInactive": False,
            },
        )
        users = data if isinstance(data, list) else []
        result = [
            {
                "username": u.get("name"),
                "account_id": u.get("accountId"),
                "display_name": u.get("displayName"),
                "email": u.get("emailAddress"),
                "active": u.get("active"),
                "timezone": u.get("timeZone"),
            }
            for u in users
        ]
        return json.dumps(
            {
                "query": params.query,
                "total": len(result),
                "users": result,
            },
            indent=2,
        )