"""Save search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import CATEGORIES
from peopleperhour_api_mcp.peopleperhour.tools._searches import (
    ALERTS,
    EXPERIENCE,
    LOCATIONS,
    PRICING,
    PROJECT_TYPES,
    search_row,
)

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

NOT_FOUND = "This account has no saved search with this saved_search_id."

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "saved_search_id": {
            "type": "string",
            "description": "Change this saved search (from list_saved_searches) instead of making a new one.",
        },
        "title": {"type": "string", "description": "Name of the saved search. Required for a new one."},
        "alert": {
            "type": "string",
            "enum": ALERTS,
            "description": "How often PeoplePerHour emails new matches to this account. Default for a new one: Daily.",
        },
        "query": {"type": "string", "description": "Keywords. New searches only."},
        "category": {"type": "string", "enum": sorted(CATEGORIES), "description": "Top category. New searches only."},
        "experience_level": {
            "type": "string",
            "enum": list(EXPERIENCE),
            "description": "Experience level the buyer asked for. New searches only.",
        },
        "pricing": {"type": "string", "enum": PRICING, "description": "Fixed price or hourly. New searches only."},
        "location": {"type": "string", "enum": LOCATIONS, "description": "Remote or onsite. New searches only."},
        "project_types": {
            "type": "array",
            "items": {"type": "string", "enum": list(PROJECT_TYPES)},
            "description": "Urgent, with no proposals yet, pre-funded, featured or high value. New searches only.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "saved_search_id": "861203",
    "title": "Logo projects",
    "alert": "Daily",
    "filters": {
        "query": "logo",
        "category": "design",
        "experience_level": "expert",
        "pricing": "fixed_price",
        "location": None,
        "project_types": ["urgent"],
    },
    "created_at": "2026-10-22T19:40:12Z",
}

_FILTERS = ("query", "category", "experience_level", "pricing", "location", "project_types")


def _new_body(args: dict[str, Any]) -> dict[str, Any]:
    """The Jobs page's form: one experience level, projectType comma-separated (an array is a server error)."""
    title = (args.get("title") or "").strip()
    if not title:
        raise ToolError("title is required for a new saved search.", ErrorCode.INVALID_INPUT)
    body: dict[str, Any] = {"title": title, "alert": args.get("alert") or "Daily", "type": "Job"}
    if query := (args.get("query") or "").strip():
        body["keyword"] = query
    if category := args.get("category"):
        body["category"] = CATEGORIES[category]
    if level := args.get("experience_level"):
        body["experience"] = str(EXPERIENCE[level])
    if pricing := args.get("pricing"):
        body["pricing"] = pricing
    if location := args.get("location"):
        body["location"] = location
    if types := args.get("project_types"):
        body["projectType"] = ",".join(PROJECT_TYPES[name] for name in types)
    return body


async def _current(ctx: ToolContext, search_id: str) -> dict[str, Any]:
    """The saved search as list_saved_searches returns it (10 per account, so a few pages at most)."""
    for page in range(1, 4):
        body = await v2(ctx, "GET", "/user/savedSearches", params={"page[number]": page})
        found = items(body)
        for item in found:
            if str(item.get("id")) == search_id:
                return search_row(item)
        if not (body.get("links") or {}).get("next"):
            break
    raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)


@tool(
    name="save_search",
    title="Save search",
    access="write",
    confirm=False,
    description="Save a project search with an email alert, or rename one or change how often it emails.",
    details=(
        "Without saved_search_id it saves a new project search on the signed-in account, as Save on the Jobs page "
        "does: title, filters and an email alert (Never, Daily or Instantly) that PeoplePerHour sends to this "
        "account only. With saved_search_id it changes only the title and the alert of that search; PeoplePerHour "
        "keeps its filters, so make a new search for other filters and delete the old one. PeoplePerHour allows "
        "10 saved searches per account."
    ),
    input_schema=INPUT_SCHEMA,
    route="POST /saved-searches",
    example_response=EXAMPLE_RESPONSE,
)
async def save_search(ctx: ToolContext, args: dict[str, Any]) -> Any:
    search_id = str(args.get("saved_search_id") or "").strip()
    if not search_id:
        answer = await v2(ctx, "POST", "/memberSavedSearches", json=_new_body(args))
        data = answer.get("data") if isinstance(answer, dict) else None
        if not isinstance(data, dict) or not data.get("id"):
            raise ToolError("PeoplePerHour did not save the search. Try again later.", ErrorCode.TARGET_ERROR)
        return search_row(data)
    if not search_id.isdigit():
        raise ToolError("saved_search_id must come from list_saved_searches.", ErrorCode.INVALID_INPUT)
    if any(args.get(name) for name in _FILTERS):
        raise ToolError(
            "A saved search keeps its filters: change only title or alert, or save a new search.",
            ErrorCode.INVALID_INPUT,
        )
    if not args.get("title") and not args.get("alert"):
        raise ToolError("Give a new title or alert for the saved search.", ErrorCode.INVALID_INPUT)
    current = await _current(ctx, search_id)
    body = {
        "title": (args.get("title") or "").strip() or current["title"],
        "alert": args.get("alert") or current["alert"],
        "type": "Job",
    }
    await v2(ctx, "PUT", f"/memberSavedSearches/{search_id}", json=body, not_found=NOT_FOUND)
    return await _current(ctx, search_id)
