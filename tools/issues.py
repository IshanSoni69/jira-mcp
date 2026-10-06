"""Jira issue-related MCP tools."""

import json
import logging
from typing import Any

from mcp.server.mcpserver.server import MCPServer as FastMCP

from jira_client import jira_delete, jira_get, jira_post, jira_put
from models import (
    AddCommentInput,
    AddWatcherInput,
    AssignIssueInput,
    CreateIssueInput,
    DeleteIssueInput,
    GetChangelogInput,
    GetCommentsInput,
    GetIssueInput,
    GetTransitionsInput,
    TransitionIssueInput,
    UpdateIssueInput,
)

logger = logging.getLogger(__name__)


def register_issue_tools(mcp: FastMCP) -> None:
    """Register all issue-related tools on the MCP server instance.

    Args:
        mcp: FastMCP server instance to register tools on.
    """

    @mcp.tool(
        name="jira_get_issue",
        annotations={
            "title": "Get Jira issue",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_issue(params: GetIssueInput) -> str:
        """Fetch a single Jira issue by its key.

        Returns full issue details including summary, status, assignee, description,
        comments count, priority, labels, components, and custom fields.

        Args:
            params: GetIssueInput with issue_key and optional fields filter.

        Returns:
            JSON string with issue details.
        """
        query: dict[str, str] = {
            "fields": params.fields if params.fields else "*all",
            "expand": "names",
        }
        data = await jira_get(f"/issue/{params.issue_key}", params=query)
        fields = data.get("fields", {})
        names: dict[str, str] = data.get("names", {})

        def _extract(val: Any) -> Any:
            """Recursively simplify a Jira field value to a scalar/list."""
            if val is None:
                return None
            if isinstance(val, list):
                return [_extract(v) for v in val]
            if isinstance(val, dict):
                for key in ("displayName", "name", "value", "key", "accountId"):
                    if key in val:
                        return val[key]
                return val
            return val

        # Known fields mapped to friendly names
        _known = {
            "customfield_11222": "story_points",
            "customfield_11224": "sprint",
            "customfield_11225": "epic_link",
            "customfield_12027": "acceptance_criteria",
            "customfield_12479": "it_team",
            "customfield_14429": "po_approved",
            "customfield_14430": "po_approved_by",
            "customfield_14431": "po_approved_date",
            "customfield_17220": "work_id",
            "customfield_17620": "system_list",
            "customfield_20323": "test_levels",
        }

        result = {
            "key": data.get("key"),
            "id": data.get("id"),
            "url": f"{data.get('self', '').split('/rest')[0]}/browse/{data.get('key')}",
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name") if fields.get("status") else None,
            "issue_type": fields.get("issuetype", {}).get("name") if fields.get("issuetype") else None,
            "priority": fields.get("priority", {}).get("name") if fields.get("priority") else None,
            "assignee": (
                fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None
            ),
            "reporter": (
                fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None
            ),
            "project": fields.get("project", {}).get("key") if fields.get("project") else None,
            "description": fields.get("description"),
            "labels": fields.get("labels", []),
            "components": [c.get("name") for c in (fields.get("components") or [])],
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "resolution": (
                fields.get("resolution", {}).get("name") if fields.get("resolution") else None
            ),
            "comment_count": fields.get("comment", {}).get("total", 0) if fields.get("comment") else 0,
        }

        # Add known custom fields under friendly names
        for cf_id, friendly in _known.items():
            result[friendly] = _extract(fields.get(cf_id))

        # Collect ALL remaining custom fields using names map for labels
        custom_fields: dict[str, Any] = {}
        for key, val in fields.items():
            if not key.startswith("customfield_"):
                continue
            if key in _known:
                continue
            if val is None:
                continue
            label = names.get(key, key)
            custom_fields[label] = _extract(val)
        if custom_fields:
            result["other_custom_fields"] = custom_fields

        return json.dumps(result, indent=2, default=str)

    @mcp.tool(
        name="jira_create_issue",
        annotations={
            "title": "Create Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def jira_create_issue(params: CreateIssueInput) -> str:
        """Create a new Jira issue.

        Creates an issue in the specified project with the given fields. Returns
        the created issue key and URL.

        Args:
            params: CreateIssueInput with project_key, summary, and optional fields.

        Returns:
            JSON string with created issue key, id, and URL.
        """
        fields: dict[str, Any] = {
            "project": {"key": params.project_key},
            "summary": params.summary,
            "issuetype": {"name": params.issue_type},
        }
        if params.description:
            fields["description"] = params.description
        if params.priority:
            fields["priority"] = {"name": params.priority}
        if params.assignee_name:
            fields["assignee"] = {"name": params.assignee_name}
        if params.labels:
            fields["labels"] = params.labels
        if params.components:
            fields["components"] = [{"name": c} for c in params.components]
        if params.story_points is not None:
            fields["story_points"] = params.story_points
            fields["customfield_10016"] = params.story_points
        if params.parent_key:
            fields["parent"] = {"key": params.parent_key}
        if params.acceptance_criteria:
            fields["customfield_12027"] = params.acceptance_criteria

        data = await jira_post("/issue", json={"fields": fields})
        base_url = next(
            (v for k, v in data.items() if k == "self"), ""
        ).split("/rest")[0]
        return json.dumps(
            {
                "key": data.get("key"),
                "id": data.get("id"),
                "url": f"{base_url}/browse/{data.get('key')}",
                "message": f"Issue {data.get('key')} created successfully.",
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_update_issue",
        annotations={
            "title": "Update Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_update_issue(params: UpdateIssueInput) -> str:
        """Update one or more fields on an existing Jira issue.

        Only fields provided (non-None) will be updated. Supports updating
        summary, description, priority, assignee, labels, and story points.

        Args:
            params: UpdateIssueInput with issue_key and fields to update.

        Returns:
            JSON string confirming success.
        """
        fields: dict[str, Any] = {}
        if params.summary is not None:
            fields["summary"] = params.summary
        if params.description is not None:
            fields["description"] = params.description
        if params.priority is not None:
            fields["priority"] = {"name": params.priority}
        if params.assignee_name is not None:
            fields["assignee"] = {"name": params.assignee_name} if params.assignee_name else None
        if params.labels is not None:
            fields["labels"] = params.labels
        if params.story_points is not None:
            fields["story_points"] = params.story_points
            fields["customfield_10016"] = params.story_points
        if params.acceptance_criteria is not None:
            fields["customfield_12027"] = params.acceptance_criteria

        if not fields:
            return json.dumps({"message": "No fields to update were provided."})

        await jira_put(f"/issue/{params.issue_key}", json={"fields": fields})
        return json.dumps(
            {
                "message": f"Issue {params.issue_key} updated successfully.",
                "updated_fields": list(fields.keys()),
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_delete_issue",
        annotations={
            "title": "Delete Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def jira_delete_issue(params: DeleteIssueInput) -> str:
        """Permanently delete a Jira issue.

        WARNING: This action is irreversible. The issue and all its data will be deleted.
        Optionally deletes sub-tasks as well.

        Args:
            params: DeleteIssueInput with issue_key and delete_subtasks flag.

        Returns:
            JSON string confirming deletion.
        """
        path = f"/issue/{params.issue_key}"
        if params.delete_subtasks:
            path += "?deleteSubtasks=true"
        await jira_delete(path)
        return json.dumps(
            {
                "message": f"Issue {params.issue_key} deleted successfully.",
                "subtasks_deleted": params.delete_subtasks,
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_get_transitions",
        annotations={
            "title": "Get Issue Transitions",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_transitions(params: GetTransitionsInput) -> str:
        """List all available workflow transitions for a Jira issue.

        Use this to get transition IDs before calling jira_transition_issue.
        Transitions represent status changes like 'To Do' -> 'In Progress'.

        Args:
            params: GetTransitionsInput with issue_key.

        Returns:
            JSON string listing available transitions with id, name, and to-status.
        """
        data = await jira_get(f"/issue/{params.issue_key}/transitions")
        transitions = [
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "to_status": t.get("to", {}).get("name") if t.get("to") else None,
            }
            for t in data.get("transitions", [])
        ]
        return json.dumps(
            {
                "issue_key": params.issue_key,
                "transitions": transitions,
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_transition_issue",
        annotations={
            "title": "Transition Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def jira_transition_issue(params: TransitionIssueInput) -> str:
        """Move a Jira issue to a new workflow status using a transition.

        First call jira_get_transitions to retrieve valid transition IDs.
        Optionally adds a comment and/or resolution during the transition.

        Args:
            params: TransitionIssueInput with issue_key, transition_id, and optional comment/resolution.

        Returns:
            JSON string confirming the transition.
        """
        body: dict[str, Any] = {"transition": {"id": params.transition_id}}
        if params.comment:
            body["update"] = {
                "comment": [{"add": {"body": params.comment}}]
            }
        if params.resolution:
            body.setdefault("fields", {})["resolution"] = {"name": params.resolution}

        await jira_post(f"/issue/{params.issue_key}/transitions", json=body)
        return json.dumps(
            {
                "message": f"Issue {params.issue_key} transitioned successfully.",
                "transition_id": params.transition_id,
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_add_comment",
        annotations={
            "title": "Add Comment to Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def jira_add_comment(params: AddCommentInput) -> str:
        """Add a comment to a Jira issue.

        The comment body supports plain text or Jira wiki markup syntax.

        Args:
            params: AddCommentInput with issue_key and body text.

        Returns:
            JSON string with the created comment ID and author.
        """
        data = await jira_post(
            f"/issue/{params.issue_key}/comment",
            json={"body": params.body},
        )
        return json.dumps(
            {
                "comment_id": data.get("id"),
                "issue_key": params.issue_key,
                "author": data.get("author", {}).get("displayName"),
                "created": data.get("created"),
                "message": "Comment added successfully.",
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_get_comments",
        annotations={
            "title": "Get Jira Issue Comments",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_comments(params: GetCommentsInput) -> str:
        """Retrieve all comments on a Jira issue.

        Returns comments with author, timestamp, and body text, ordered by creation date.

        Args:
            params: GetCommentsInput with issue_key and max_results.

        Returns:
            JSON string listing comments.
        """
        data = await jira_get(
            f"/issue/{params.issue_key}/comment",
            params={"maxResults": params.max_results, "orderBy": "created"},
        )
        comments = [
            {
                "id": c.get("id"),
                "author": c.get("author", {}).get("displayName"),
                "body": c.get("body"),
                "created": c.get("created"),
                "updated": c.get("updated"),
            }
            for c in data.get("comments", [])
        ]
        return json.dumps(
            {
                "issue_key": params.issue_key,
                "total": data.get("total", len(comments)),
                "comments": comments,
            },
            indent=2,
            default=str,
        )

    @mcp.tool(
        name="jira_assign_issue",
        annotations={
            "title": "Assign Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_assign_issue(params: AssignIssueInput) -> str:
        """Assign a Jira issue to a user or unassign it.

        Pass assignee_name as None or empty string to unassign.

        Args:
            params: AssignIssueInput with issue_key and optional assignee_name.

        Returns:
            JSON string confirming the assignment.
        """
        body: dict[str, Any] = {
            "name": params.assignee_name if params.assignee_name else None
        }
        await jira_put(f"/issue/{params.issue_key}/assignee", json=body)
        msg = (
            f"Issue {params.issue_key} assigned to {params.assignee_name}."
            if params.assignee_name
            else f"Issue {params.issue_key} unassigned."
        )
        return json.dumps({"message": msg, "issue_key": params.issue_key}, indent=2)

    @mcp.tool(
        name="jira_add_watcher",
        annotations={
            "title": "Add Watcher to Jira Issue",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_add_watcher(params: AddWatcherInput) -> str:
        """Add a user as a watcher on a Jira issue.

        Watchers receive notifications when the issue is updated.

        Args:
            params: AddWatcherInput with issue_key and username.

        Returns:
            JSON string confirming the watcher was added.
        """
        await jira_post(
            f"/issue/{params.issue_key}/watchers",
            json=params.username,
        )
        return json.dumps(
            {
                "message": f"User '{params.username}' added as watcher to {params.issue_key}.",
                "issue_key": params.issue_key,
            },
            indent=2,
        )

    @mcp.tool(
        name="jira_get_issue_changelog",
        annotations={
            "title": "Get Jira Issue Changelog",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": True,
        },
    )
    async def jira_get_issue_changelog(params: GetChangelogInput) -> str:
        """Retrieve the full change history/changelog of a Jira issue.

        Returns a list of change events showing who changed what and when,
        including status changes, field edits, and assignments.

        Args:
            params: GetChangelogInput with issue_key and max_results.

        Returns:
            JSON string with chronological list of change events.
        """
        data = await jira_get(
            f"/issue/{params.issue_key}/changelog",
            params={"maxResults": params.max_results},
        )
        histories = [
            {
                "id": h.get("id"),
                "author": h.get("author", {}).get("displayName"),
                "created": h.get("created"),
                "items": [
                    {
                        "field": i.get("field"),
                        "from": i.get("fromString"),
                        "to": i.get("toString"),
                    }
                    for i in h.get("items", [])
                ],
            }
            for h in data.get("values", data.get("histories", []))
        ]
        return json.dumps(
            {
                "issue_key": params.issue_key,
                "total": data.get("total", len(histories)),
                "changelog": histories,
            },
            indent=2,
            default=str,
        )