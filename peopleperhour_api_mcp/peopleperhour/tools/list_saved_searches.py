"""List saved searches."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._searches import search_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"cursor": {"type": "string", "description": "next_cursor from the previous call."}},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "saved_searches": [
        {
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
    ],
    "next_cursor": None,
}


@tool(
    name="list_saved_searches",
    title="List saved searches",
    access="read",
    confirm=False,
    description="This account's saved project searches with their filters and email alert setting.",
    details=(
        "Returns the project searches the signed-in account saved on the Jobs page: title, email alert (Never, "
        "Daily or Instantly) and filters. filters.query and filters.category can go straight into search_projects. "
        "PeoplePerHour allows 10 saved searches per account."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /saved-searches",
    example_response=EXAMPLE_RESPONSE,
)
async def list_saved_searches(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page = page_cursor(args.get("cursor"))
    body = await v2(ctx, "GET", "/user/savedSearches", params={"page[number]": page})
    rows = [search_row(item) for item in items(body)]
    return {"saved_searches": rows, "next_cursor": next_page(body, page) if rows else None}
