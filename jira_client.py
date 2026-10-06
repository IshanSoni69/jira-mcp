"""Jira REST API v2 async client with PAT Bearer authentication."""

from ast import Raise
from enum import verify
import logging
import os
from typing import Any
from wsgiref import headers
import httpx
from regex import V1

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)
JIRA_URL = os.environ.get("JIRA_URL", "https://jira.elevancehealth.com").rstrip("/")
JIRA_PAT = os.environ.get("JIRA_PAT", "")

_API_V2 = f"{JIRA_URL}/rest/api/2"
_AGILE_V1 = f"{JIRA_URL}/rest/agile/1.0"

def _build_client() -> httpx.AsyncClient:
    """Create a configured httpx async client for Jira REST API v2."""
    if not JIRA_PAT:
        raise RuntimeError(
            "JIRA PAT environment variable is not set. "
            "Generate a PAT at your Jira profile Personal Access Tokens."
        )

    headers = {
        "Authorization": f"Bearer {JIRA_PAT}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    return httpx.AsyncClient(headers=headers, timeout=30.0, verify=False)

def _raise_for_status(response: httpx.Response) -> None:
    """Raise a descriptive RuntimeError on non-2xxx responses."""
    if response.is_success:
        return
    
    try:
        body = response.json()
        messages = body.get("errorMessages", [])
        errors = body.get("errors", ())
        detail = "; ".join(messages) if messages else str(errors) if errors else response.text[:500]
    except Exception:
        detail = response.text[:500]
    raise RuntimeError(
        f"Jira API error {response.status_code} [{response.request.method} {response.request.url}] : {detail}"
    )

async def jira_get(path: str, params: dict[str, Any] | list[tuple[str, str]] | None = None) -> Any:
    """Perform a GET request against Jira REST API v2.

    Args:
        path: Relative path appended to the API v2 base, e.g. "/issue/PROJ-1".
        params: Optional query parameters.

    Returns:
        Parsed JSON response body.
    """
    async with _build_client() as client:
        url = f"{_API_V2}{path}"
        logger.debug("GET %s params=%s", url, params)
        response = await client.get(url, params=params)
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()


async def jira_post(path: str, json: dict[str, Any] | None = None) -> Any:
    """Perform a POST request against Jira REST API v2.

    Args:
        path: Relative path appended to the API v2 base.
        json: JSON request body.

    Returns:
        Parsed JSON response body.
    """
    async with _build_client() as client:
        url = f"{_API_V2}{path}"
        logger.debug("POST %s body=%s", url, json)
        response = await client.post(url, json=json or {})
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()


async def jira_put(path: str, json: dict[str, Any] | None = None) -> Any:
    """Perform a PUT request against Jira REST API v2.

    Args:
        path: Relative path appended to the API v2 base.
        json: JSON request body.

    Returns:
        Parsed JSON response body (empty dict if 204).
    """
    async with _build_client() as client:
        url = f"{_API_V2}{path}"
        logger.debug("PUT %s body=%s", url, json)
        response = await client.put(url, json=json or {})
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()


async def jira_delete(path: str) -> dict[str, Any]:
    """Perform a DELETE request against Jira REST API v2.

    Args:
        path: Relative path appended to the API v2 base.

    Returns:
        Empty dict on success (204 No Content).
    """
    async with _build_client() as client:
        url = f"{_API_V2}{path}"
        logger.debug("DELETE %s", url)
        response = await client.delete(url)
        _raise_for_status(response)
        return {}


async def agile_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """Perform a GET request against Jira Agile REST API v1.

    Args:
        path: Relative path appended to the Agile v1 base.
        params: Optional query parameters.

    Returns:
        Parsed JSON response body.
    """
    async with _build_client() as client:
        url = f"{_AGILE_V1}{path}"
        logger.debug("GET (agile) %s params=%s", url, params)
        response = await client.get(url, params=params)
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()


async def agile_post(path: str, json: dict[str, Any] | None = None) -> Any:
    """Perform a POST request against Jira Agile REST API v1.

    Args:
        path: Relative path appended to the Agile v1 base.
        json: JSON request body.

    Returns:
        Parsed JSON response body.
    """
    async with _build_client() as client:
        url = f"{_AGILE_V1}{path}"
        logger.debug("POST (agile) %s body=%s", url, json)
        response = await client.post(url, json=json or {})
        _raise_for_status(response)
        if response.status_code == 204 or not response.content:
            return {}
        return response.json()
