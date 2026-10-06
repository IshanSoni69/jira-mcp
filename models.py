"""Shared Pydantic input models for Jira MCP tools."""

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class _Base(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )


# ------------------------------------------------------------------------------
# Issue models
# ------------------------------------------------------------------------------


class GetIssueInput(_Base):
    """Input for fetching a single Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    fields: Optional[str] = Field(
        default=None,
        description="Comma-separated list of fields to return (default: all). E.g. 'summary,status,assignee'",
    )


class CreateIssueInput(_Base):
    """Input for creating a new Jira issue."""

    project_key: str = Field(
        ...,
        description="Project key where the issue is created, e.g. 'PROJ'",
        min_length=1,
        max_length=20,
    )
    summary: str = Field(
        ...,
        description="One-line summary/title of the issue",
        min_length=1,
        max_length=255,
    )
    issue_type: str = Field(
        default="Task",
        description="Issue type name, e.g. 'Bug', 'Story', 'Task', 'Epic'",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed description of the issue (plain text or Jira wiki markup)",
    )
    priority: Optional[str] = Field(
        default=None,
        description="Priority name, e.g. 'High', 'Medium', 'Low', 'Critical'",
    )
    assignee_name: Optional[str] = Field(
        default=None,
        description="Username of the assignee, e.g. 'AH05391'",
    )
    labels: Optional[list[str]] = Field(
        default=None,
        description="List of labels to apply to the issue",
    )
    components: Optional[list[str]] = Field(
        default=None,
        description="List of component names to associate with the issue",
    )
    story_points: Optional[float] = Field(
        default=None,
        description="Story points / estimation (uses 'story_points' custom field)",
        ge=0,
    )
    parent_key: Optional[str] = Field(
        default=None,
        description="Parent issue key (for sub-tasks or child issues), e.g. 'PROJ-10'",
    )
    acceptance_criteria: Optional[str] = Field(
        default=None,
        description=(
            "Acceptance criteria for the issue (plain text or Jira wiki markup). "
            "Stored in customfield_12027 (Jira Acceptance Criteria custom field)."
        ),
    )


class UpdateIssueInput(_Base):
    """Input for updating fields on an existing Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key to update, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    summary: Optional[str] = Field(default=None, description="New summary/title")
    description: Optional[str] = Field(default=None, description="New description")
    priority: Optional[str] = Field(
        default=None,
        description="New priority name, e.g. 'High'",
    )
    assignee_name: Optional[str] = Field(
        default=None,
        description="New assignee username; pass empty string to unassign",
    )
    labels: Optional[list[str]] = Field(
        default=None,
        description="Replace all labels with this list",
    )
    story_points: Optional[float] = Field(
        default=None,
        description="New story points value",
        ge=0,
    )
    acceptance_criteria: Optional[str] = Field(
        default=None,
        description=(
            "Updated acceptance criteria (plain text or Jira wiki markup). "
            "Stored in customfield_12027 (Jira Acceptance Criteria custom field)."
        ),
    )


class DeleteIssueInput(_Base):
    """Input for deleting a Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key to delete, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    delete_subtasks: bool = Field(
        default=False,
        description="Whether to also delete all sub-tasks of this issue",
    )


class TransitionIssueInput(_Base):
    """Input for transitioning a Jira issue to a new status."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    transition_id: str = Field(
        ...,
        description="Transition ID obtained from jira_get_transitions, e.g. '21'",
        min_length=1,
    )
    comment: Optional[str] = Field(
        default=None,
        description="Optional comment to add when transitioning",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Resolution name if required (e.g. 'Done', 'Won\\'t Fix')",
    )


class GetTransitionsInput(_Base):
    """Input for listing available transitions for an issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )


class AddCommentInput(_Base):
    """Input for adding a comment to a Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    body: str = Field(
        ...,
        description="Comment text (plain text or Jira wiki markup)",
        min_length=1,
    )


class GetCommentsInput(_Base):
    """Input for retrieving comments on a Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of comments to return",
        ge=1,
        le=200,
    )


class AssignIssueInput(_Base):
    """Input for assigning a Jira issue to a user."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    assignee_name: Optional[str] = Field(
        default=None,
        description="Username to assign to. Pass null/empty to unassign.",
    )


class AddWatcherInput(_Base):
    """Input for adding a watcher to a Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    username: str = Field(
        ...,
        description="Username of the watcher to add, e.g. 'AH05391'",
        min_length=1,
    )


class GetChangelogInput(_Base):
    """Input for fetching the changelog/history of a Jira issue."""

    issue_key: str = Field(
        ...,
        description="Jira issue key, e.g. 'PROJ-123'",
        min_length=1,
        max_length=50,
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of changelog entries to return",
        ge=1,
        le=200,
    )


# ------------------------------------------------------------------------------
# Search models
# ------------------------------------------------------------------------------


class SearchIssuesInput(_Base):
    """Input for JQL search."""

    jql: str = Field(
        ...,
        description=(
            "JQL query string, e.g. 'project = PROJ AND status = Open ORDER BY created DESC'. "
            "Use Jira Query Language syntax."
        ),
        min_length=1,
    )
    fields: Optional[str] = Field(
        default="summary,status,assignee,priority,issuetype,created,updated",
        description="Comma-separated list of fields to include in results",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of results to return",
        ge=1,
        le=200,
    )
    start_at: int = Field(
        default=0,
        description="Zero-based index of the first issue to return (for pagination)",
        ge=0,
    )


class GetMyIssuesInput(_Base):
    """Input for fetching issues assigned to the current user."""

    status_category: Optional[str] = Field(
        default=None,
        description="Filter by status category: 'To Do', 'In Progress', 'Done', or None for all",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of issues to return",
        ge=1,
        le=200,
    )


# ------------------------------------------------------------------------------
# Project models
# ------------------------------------------------------------------------------


class GetProjectInput(_Base):
    """Input for getting a single project."""

    project_key: str = Field(
        ...,
        description="Jira project key, e.g. 'PROJ'",
        min_length=1,
        max_length=20,
    )


class ListProjectsInput(_Base):
    """Input for listing all accessible projects."""

    max_results: int = Field(
        default=50,
        description="Maximum number of projects to return",
        ge=1,
        le=200,
    )
    project_type: Optional[str] = Field(
        default=None,
        description="Filter by project type (e.g. 'software', 'service_desk')",
    )

class GetProjectIssueTypesInput(_Base):
    """Input for listing issue types for a project."""

    project_key: str = Field(
        ...,
        description="Jira project key, e.g. 'PROJ'",
        min_length=1,
        max_length=20,
    )


class GetProjectStatusesInput(_Base):
    """Input for listing statuses/workflows for a project."""

    project_key: str = Field(
        ...,
        description="Jira project key, e.g. 'PROJ'",
        min_length=1,
        max_length=20,
    )


# ------------------------------------------------------------------------------
# Agile models
# ------------------------------------------------------------------------------


class GetBoardsInput(_Base):
    """Input for listing Agile boards."""

    project_key: Optional[str] = Field(
        default=None,
        description="Filter boards by project key, e.g. 'PROJ'",
    )
    board_type: Optional[str] = Field(
        default=None,
        description="Board type filter: 'scrum', 'kanban', or 'simple'",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of boards to return",
        ge=1,
        le=100,
    )


class GetSprintsInput(_Base):
    """Input for listing sprints on a board."""

    board_id: int = Field(
        ...,
        description="Numeric board ID obtained from jira_get_boards",
        ge=1,
    )
    state: Optional[str] = Field(
        default=None,
        description="Sprint state filter: 'active', 'future', 'closed'",
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of sprints to return",
        ge=1,
        le=100,
    )


class GetSprintIssuesInput(_Base):
    """Input for listing issues in a sprint."""

    sprint_id: int = Field(
        ...,
        description="Numeric sprint ID obtained from jira_get_sprints",
        ge=1,
    )
    max_results: int = Field(
        default=50,
        description="Maximum number of issues to return",
        ge=1,
        le=200,
    )
    fields: Optional[str] = Field(
        default="summary,status,assignee,priority,issuetype,story_points",
        description="Comma-separated list of fields to include",
    )


class MoveIssueToSprintInput(_Base):
    """Input for moving an issue to a sprint."""

    issue_keys: list[str] = Field(
        ...,
        description="List of issue keys to move, e.g. ['PROJ-1', 'PROJ-2']",
        min_length=1,
    )
    sprint_id: int = Field(
        ...,
        description="Target sprint ID obtained from jira_get_sprints",
        ge=1,
    )


# ------------------------------------------------------------------------------
# User models
# ------------------------------------------------------------------------------


class SearchUsersInput(_Base):
    """Input for searching Jira users."""

    query: str = Field(
        ...,
        description="Search string (name, username, or email fragment), e.g. 'Ishan' or 'AL58368'",
        min_length=1,
    )
    max_results: int = Field(
        default=20,
        description="Maximum number of users to return",
        ge=1,
    )
