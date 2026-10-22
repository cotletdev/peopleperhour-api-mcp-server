"""List watchlist."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import limit, page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import included, items, me, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import excerpt, project_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "limit": {"type": "integer", "description": "1 to 50. Default: 20. Keep it the same across pages."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "projects": [
        {
            "project_id": "4527860",
            "title": "Website design",
            "url": "https://www.peopleperhour.com/freelance-jobs/design/web-design/website-design-4527860",
            "budget": {"amount": 70, "currency": "EUR", "type": "fixed_price"},
            "category": "Design",
            "subcategory": "Web Design",
            "experience_level": "entry",
            "location_type": "remote",
            "freelancer_country": None,
            "urgent": False,
            "featured": False,
            "proposals": 42,
            "posted_at": "2026-10-22T08:22:55Z",
            "expires_at": "2026-11-21T08:22:55Z",
            "excerpt": "We are a small business looking for a simple website with five pages and a contact form…",
        }
    ],
    "total": 1,
    "next_cursor": None,
}


@tool(
    name="list_watchlist",
    title="List watchlist",
    access="read",
    confirm=False,
    description="Open projects on this account's watchlist (Favourite Jobs), with budget and proposal count.",
    details=(
        "Returns the open projects the signed-in account watches, in the same shape as search_projects. A watched "
        "project that has closed drops off the list. Pass next_cursor back as cursor with the same limit; it is "
        "null on the last page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/watched",
    example_response=EXAMPLE_RESPONSE,
)
async def list_watchlist(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page, size = page_cursor(args.get("cursor")), limit(args, 20, 50)
    member_id = str((await me(ctx))["id"])
    query = {
        "filter[dataset]": "starred",
        "include": "watchlists",
        "withoutFacets": 1,
        "page[number]": page,
        "page[size]": size,
    }
    body = await v2(ctx, "GET", "/projects/listAll", params=query)
    # An empty watchlist makes `filter[dataset]=starred` answer every open project, and the favourites count lags
    # behind a watch by minutes, so keep only projects whose watchers include this member.
    mine = {
        str(w.get("project_id")) for w in included(body, "projectsWatchlists") if str(w.get("member_id")) == member_id
    }
    rows = [
        {**project_row(attrs), "excerpt": excerpt(attrs.get("proj_desc"))}
        for attrs in (item.get("attributes") or {} for item in items(body))
        if str(attrs.get("proj_id")) in mine
    ]
    if not rows:
        return {"projects": [], "total": 0, "next_cursor": None}
    total = (body.get("meta") or {}).get("total-items")
    return {
        "projects": rows,
        "total": total if isinstance(total, int) else len(rows),
        "next_cursor": next_page(body, page),
    }
