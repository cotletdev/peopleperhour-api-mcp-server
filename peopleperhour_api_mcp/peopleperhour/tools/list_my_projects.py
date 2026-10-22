"""List my projects."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import excerpt, project_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

# `meta.filters.item_state` of GET /v2/projects (22.10.2026).
STATES = [
    "open",
    "in_progress",
    "under_moderation",
    "paused",
    "awarded",
    "completed",
    "expired",
    "cancelled",
    "archived",
]

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": STATES, "description": "Only projects in this state."},
        "query": {"type": "string", "description": "Words in the project title."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "projects": [
        {
            "project_id": "4527990",
            "title": "Logo for a coffee shop",
            "url": "https://www.peopleperhour.com/freelance-jobs/design/logo-design/logo-for-a-coffee-shop-4527990",
            "budget": {"amount": 120, "currency": "GBP", "type": "fixed_price"},
            "category": "Design",
            "subcategory": "Logo Design",
            "experience_level": "intermediate",
            "location_type": "remote",
            "freelancer_country": None,
            "urgent": False,
            "featured": False,
            "proposals": 12,
            "posted_at": "2026-10-20T09:14:00Z",
            "expires_at": "2026-11-19T09:14:00Z",
            "status": "open",
            "excerpt": "A simple, warm logo for a small coffee shop…",
        }
    ],
    "counts": {
        "open": 1,
        "in_progress": 0,
        "under_moderation": 0,
        "paused": 0,
        "awarded": 0,
        "completed": 0,
        "expired": 0,
        "cancelled": 0,
        "archived": 0,
    },
    "next_cursor": None,
}


@tool(
    name="list_my_projects",
    title="List my projects",
    access="read",
    confirm=False,
    description="Projects this account posted as a buyer, with status, budget and proposal count.",
    details=(
        "Returns the projects the signed-in buyer posted, most recent proposal first, each with its status (open, "
        "in_progress, under_moderation, completed and so on), budget, proposal count and the start of the brief. "
        "counts is the number of projects per status. Archived projects come back only with status archived. "
        "Pass next_cursor back as cursor; it is null on the last page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/mine",
    example_response=EXAMPLE_RESPONSE,
)
async def list_my_projects(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page = page_cursor(args.get("cursor"))
    query: dict[str, Any] = {"page[number]": page, "sort": "recent_proposal"}
    if status := args.get("status"):
        query["filter[item_state]"] = status
        if status == "archived":
            query["include_archived"] = 1
    if words := (args.get("query") or "").strip():
        query["filter[search_term]"] = words
    body = await v2(ctx, "GET", "/projects", params=query)
    rows = [
        {**project_row(attrs), "status": attrs.get("item_state") or None, "excerpt": excerpt(attrs.get("proj_desc"))}
        for attrs in (item.get("attributes") or {} for item in items(body))
    ]
    facets = (body.get("meta") or {}).get("facets") or {}
    return {
        "projects": rows,
        "counts": {state: facets[state] for state in STATES if isinstance(facets.get(state), int)},
        "next_cursor": next_page(body, page) if rows else None,
    }
