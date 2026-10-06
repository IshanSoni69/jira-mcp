"""Jira JQL search MCP tools."""

import json
import logging

# from mcp.server.mcpserver.server import MCPServer as FastMCP
from mcp.server import MCPServer as FastMCP

from jira_client import jira_post
from models import GetMyIssuesInput, SearchIssuesInput

logger = logging.getLogger(__name__)

_DEFAULT_FIELDS = "summary,status,assignee,priority,issuetype,created,updated,labels,components"


def _format_issue(issue: dict) -> dict:
    """Extract key display fields from a raw Jira issue dict.

    Args:
        issue: Raw issue object from the Jira REST API response.

    Returns:
        Dict with selected, flattened fields for display.
    """
    fields = issue.get("fields", {})
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name") if fields.get("status") else None,
        "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
        "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
        "assignee": (
            fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
        ),
        "labels": fields.get("labels", []),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
    }


def register_search_tools(mcp: FastMCP) -> None:
    """Register JQL search tools on the MCP server instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(
        name="jira_search_issues",
        annotations={
            "title": "Search Jira Issues with JQL",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_search_issues(params: SearchIssuesInput) -> str:
        """Search Jira issues using JQL (Jira Query Language).

        Supports pagination via start_at. JQL examples:
        - 'project = PROJ AND status = "In Progress"'
        - 'assignee = currentUser() ORDER BY updated DESC'
        - 'labels = backend AND created >= -7d'
        - 'sprint in openSprints() AND project = PROJ'

        Args:
            params: SearchIssuesInput with jql query, fields, max_results, and start_at.

        Returns:
            JSON string with matched issues and pagination info.
        """
        body = {
            "jql": params.jql,
            "startAt": params.start_at,
            "maxResults": params.max_results,
            "fields": [f.strip() for f in (params.fields or _DEFAULT_FIELDS).split(",")],
        }
        data = await jira_post("/search", json=body)
        issues = [_format_issue(i) for i in data.get("issues", [])]
        return json.dumps(
            {
                "jql": params.jql,
                "total": data.get("total", 0),
                "start_at": data.get("startAt", 0),
                "max_results": data.get("maxResults", params.max_results),
                "returned": len(issues),
                "issues": issues,
            },
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_get_my_issues",
        annotations={
            "title": "Get My Jira Issues",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_my_issues(params: GetMyIssuesInput) -> str:
        """Fetch all Jira issues currently assigned to the authenticated user.

        Optionally filter by status category: 'To Do', 'In Progress', or 'Done'.
        Results are ordered by last updated descending.

        Args:
            params: GetMyIssuesInput with optional status_category and max_results.

        Returns:
            JSON string listing issues assigned to the current user.
        """
        jql = "assignee = currentUser()"
        if params.status_category:
            jql += f' AND statusCategory = "{params.status_category}"'
        jql += " ORDER BY updated DESC"

        body = {
            "jql": jql,
            "startAt": 0,
            "maxResults": params.max_results,
            "fields": _DEFAULT_FIELDS.split(","),
        }
        data = await jira_post("/search", json=body)
        issues = [_format_issue(i) for i in data.get("issues", [])]
        return json.dumps(
            {
                "jql": jql,
                "total": data.get("total", 0),
                "returned": len(issues),
                "issues": issues,
            },
            indent=2,
            default=str,
        )
