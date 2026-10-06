"""Jira Agile sprint MCP tools (Jira Software / Agile REST API v1)."""

import json
import logging

# from mcp.server.mcpserver.server import MCPServer as FastMCP
from mcp.server import MCPServer as FastMCP

from jira_client import agile_get, agile_post
from models import (
    GetBoardsInput,
    GetSprintIssuesInput,
    GetSprintsInput,
    MoveIssueToSprintInput,
)

logger = logging.getLogger(__name__)


def _format_issue(issue: dict) -> dict:
    """Extract display fields from a sprint issue.

    Args:
        issue: Raw Jira issue object from Agile API.

    Returns:
        Flattened dict of selected fields.
    """
    fields = issue.get("fields", {})
    return {
        "key": issue.get("key"),
        "summary": fields.get("summary"),
        "status": fields.get("status", {}).get("name") if fields.get("status") else None,
        "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
        "assignee": (
            fields.get("assignee", {}).get("displayName") if fields.get("assignee") else "Unassigned"
        ),
        "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
        "story_points": fields.get("story_points") or fields.get("customfield_10016"),
    }


def register_sprint_tools(mcp: FastMCP) -> None:
    """Register Agile sprint tools on the MCP server instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(
        name="jira_get_boards",
        annotations={
            "title": "Get Jira Agile Boards",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_boards(params: GetBoardsInput) -> str:
        """List all Agile boards (Scrum/Kanban) accessible to the authenticated user.

        Returns board IDs, names, and types. Use board IDs with jira_get_sprints.
        Optionally filter by project key or board type (scrum/kanban).

        Args:
            params: GetBoardsInput with optional project_key, board_type, and max_results.

        Returns:
            JSON string listing boards with id, name, type, and project.
        """
        query: dict = {"maxResults": params.max_results}
        if params.project_key:
            query["projectKeyOrId"] = params.project_key
        if params.board_type:
            query["type"] = params.board_type

        data = await agile_get("/board", params=query)
        boards = [
            {
                "id": b.get("id"),
                "name": b.get("name"),
                "type": b.get("type"),
                "project_key": b.get("location", {}).get("projectKey") if b.get("location") else None,
                "project_name": b.get("location", {}).get("projectName") if b.get("location") else None,
            }
            for b in data.get("values", [])
        ]
        return json.dumps(
            {"total": data.get("total", len(boards)), "boards": boards},
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_get_sprints",
        annotations={
            "title": "Get Sprints for a Board",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_sprints(params: GetSprintsInput) -> str:
        """List sprints for a specific Agile board.

        Optionally filter by sprint state: 'active', 'future', or 'closed'.
        Returns sprint IDs, names, start/end dates, and state.

        Args:
            params: GetSprintsInput with board_id, optional state, and max_results.

        Returns:
            JSON string listing sprints.
        """
        query: dict = {"maxResults": params.max_results}
        if params.state:
            query["state"] = params.state

        data = await agile_get(f"/board/{params.board_id}/sprint", params=query)
        sprints = [
            {
                "id": s.get("id"),
                "name": s.get("name"),
                "state": s.get("state"),
                "start_date": s.get("startDate"),
                "end_date": s.get("endDate"),
                "complete_date": s.get("completeDate"),
                "goal": s.get("goal"),
            }
            for s in data.get("values", [])
        ]
        return json.dumps(
            {
                "board_id": params.board_id,
                "total": data.get("total", len(sprints)),
                "sprints": sprints,
            },
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_get_sprint_issues",
        annotations={
            "title": "Get Issues in a Sprint",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_sprint_issues(params: GetSprintIssuesInput) -> str:
        """List all issues belonging to a specific Jira sprint.

        Returns issue keys, summaries, statuses, assignees, and story points.
        Use jira_get_sprints to find the sprint ID first.

        Args:
            params: GetSprintIssuesInput with sprint_id, max_results, and optional fields.

        Returns:
            JSON string listing sprint issues with summary statistics.
        """
        query: dict = {"maxResults": params.max_results}
        if params.fields:
            query["fields"] = params.fields

        data = await agile_get(f"/sprint/{params.sprint_id}/issue", params=query)
        issues = [_format_issue(i) for i in data.get("issues", [])]
        total = data.get("total", len(issues))

        done_count = sum(1 for i in issues if (i.get("status") or "").lower() == "done")
        return json.dumps(
            {
                "sprint_id": params.sprint_id,
                "total": total,
                "done": done_count,
                "remaining": len(issues) - done_count,
                "issues": issues,
            },
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_move_issue_to_sprint",
        annotations={
            "title": "Move Issues to Sprint",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_move_issue_to_sprint(params: MoveIssueToSprintInput) -> str:
        """Move one or more Jira issues to a specified sprint.

        Issues can be moved from backlog, another sprint, or any state.
        Use jira_get_sprints to find the target sprint ID.

        Args:
            params: MoveIssueToSprintInput with list of issue_keys and target sprint_id.

        Returns:
            JSON string confirming the move.
        """
        await agile_post(
            f"/sprint/{params.sprint_id}/issue",
            json={"issues": params.issue_keys},
        )
        return json.dumps(
            {
                "message": f"Moved {len(params.issue_keys)} issue(s) to sprint {params.sprint_id}.",
                "sprint_id": params.sprint_id,
                "issue_keys": params.issue_keys,
            },
            indent=2,
        )