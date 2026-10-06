"""Jira project-related MCP tools."""

import json
import logging

# from mcp.server.mcpserver.server import MCPServer as FastMCP
from mcp.server import MCPServer as FastMCP

from jira_client import jira_get
from models import (
    GetProjectInput,
    GetProjectIssueTypesInput,
    GetProjectStatusesInput,
    ListProjectsInput,
)

logger = logging.getLogger(__name__)


def register_project_tools(mcp: FastMCP) -> None:
    """Register project-related tools on the MCP server instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(
        name="jira_list_projects",
        annotations={
            "title": "List Jira Projects",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_list_projects(params: ListProjectsInput) -> str:
        """List all Jira projects accessible to the authenticated user.

        Returns project key, name, type, and lead for each project.
        Optionally filter by project type (software, business, service_desk).

        Args:
            params: ListProjectsInput with optional project_type filter and max_results.

        Returns:
            JSON string listing accessible projects.
        """
        query: dict = {
            "maxResults": params.max_results,
            "expand": "description,lead,issueTypes",
        }
        if params.project_type:
            query["typeKey"] = params.project_type

        data = await jira_get("/project", params=query)
        projects = [
            {
                "key": p.get("key"),
                "id": p.get("id"),
                "name": p.get("name"),
                "project_type": p.get("projectTypeKey"),
                "lead": p.get("lead", {}).get("displayName")
                if p.get("lead")
                else None,
                "description": p.get("description"),
                "url": p.get("self", "").split("/rest")[0] + f"/browse/{p.get('key')}",
            }
            for p in (data if isinstance(data, list) else data.get("values", []))
        ]
        return json.dumps(
            {"total": len(projects), "projects": projects},
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_get_project",
        annotations={
            "title": "Get Jira Project Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_project(params: GetProjectInput) -> str:
        """Get detailed information about a specific Jira project by its key.

        Returns project metadata including name, description, lead, issue types,
        and project category.

        Args:
            params: GetProjectInput with project_key.

        Returns:
            JSON string with project details.
        """
        data = await jira_get(
            f"/project/{params.project_key}",
            params={
                "expand": "description,lead,issueTypes,projectKeys,versions,components"
            },
        )
        base_url = data.get("self", "").split("/rest")[0]
        return json.dumps(
            {
                "key": data.get("key"),
                "id": data.get("id"),
                "name": data.get("name"),
                "description": data.get("description"),
                "project_type": data.get("projectTypeKey"),
                "lead": data.get("lead", {}).get("displayName")
                if data.get("lead")
                else None,
                "url": f"{base_url}/browse/{data.get('key')}",
                "issue_types": [
                    {
                        "id": it.get("id"),
                        "name": it.get("name"),
                        "subtask": it.get("subtask"),
                    }
                    for it in (data.get("issueTypes") or [])
                ],
                "versions": [
                    {
                        "id": v.get("id"),
                        "name": v.get("name"),
                        "released": v.get("released"),
                    }
                    for v in (data.get("versions") or [])
                ],
                "components": [
                    {"id": c.get("id"), "name": c.get("name")}
                    for c in (data.get("components") or [])
                ],
            },
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_get_project_issue_types",
        annotations={
            "title": "Get Project Issue Types",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_project_issue_types(
        params: GetProjectIssueTypesInput,
    ) -> str:
        """List all issue types available in a Jira project.

        Use this to know what issue types (Bug, Story, Task, Epic, etc.) are
        valid before creating issues in a project.

        Args:
            params: GetProjectIssueTypesInput with project_key.

        Returns:
            JSON string listing issue types with id, name, and subtask flag.
        """
        data = await jira_get(
            f"/project/{params.project_key}",
            params={"expand": "issueTypes"},
        )
        issue_types = [
            {
                "id": it.get("id"),
                "name": it.get("name"),
                "description": it.get("description"),
                "subtask": it.get("subtask", False),
                "icon_url": it.get("iconUrl"),
            }
            for it in (data.get("issueTypes") or [])
        ]
        return json.dumps(
            {
                "project_key": params.project_key,
                "issue_types": issue_types,
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_get_project_statuses",
        annotations={
            "title": "Get Project Statuses",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_project_statuses(
        params: GetProjectStatusesInput,
    ) -> str:
        """List all workflow statuses used in a Jira project grouped by issue type.

        Use this to understand what statuses are available and how they map to
        status categories (To Do, In Progress, Done).

        Args:
            params: GetProjectStatusesInput with project_key.

        Returns:
            JSON string mapping issue types to their available statuses.
        """
        data = await jira_get(f"/project/{params.project_key}/statuses")
        result = []
        for item in data if isinstance(data, list) else []:
            result.append(
                {
                    "issue_type": item.get("name"),
                    "statuses": [
                        {
                            "id": s.get("id"),
                            "name": s.get("name"),
                            "category": s.get("statusCategory", {}).get("name"),
                        }
                        for s in item.get("statuses", [])
                    ],
                }
            )

        return json.dumps(
            {"project_key": params.project_key, "issue_type_statuses": result},
            indent=2,
        )