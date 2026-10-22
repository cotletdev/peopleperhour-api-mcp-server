"""Search projects."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.helpers import limit
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import CATEGORIES, excerpt, posted, project_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

# listAll pages are always read 50 at a time (its maximum), so a cursor stays valid whatever `limit` the next call
# passes. The cursor is "<page>" or "<page>.<index on that page>".
PAGE_SIZE = 50
# With `since`, pages read per call before handing back a cursor (200 projects, about a week of new ones).
MAX_PAGES = 4
_CURSOR = re.compile(r"^(\d+)(?:\.(\d+))?$")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Keywords to search for."},
        "category": {
            "type": "string",
            "enum": sorted(CATEGORIES),
            "description": "Only projects in this top category.",
        },
        "since": {
            "type": "string",
            "format": "date-time",
            "description": "Only projects posted after this time (ISO 8601; without a zone it is UTC).",
        },
        "limit": {"type": "integer", "description": "1 to 50. Default: 20."},
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
    "next_cursor": "1.20",
}


def _position(cursor: str | None) -> tuple[int, int]:
    """(page from 1, index on that page) of a cursor we handed out."""
    if not cursor:
        return 1, 0
    match = _CURSOR.match(cursor)
    if not match or int(match.group(1)) < 1 or int(match.group(2) or 0) >= PAGE_SIZE:
        raise ToolError("cursor must be the next_cursor value from the previous call.", ErrorCode.INVALID_INPUT)
    return int(match.group(1)), int(match.group(2) or 0)


def _since(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        moment = datetime.fromisoformat(str(value).strip())
    except ValueError:
        raise ToolError("since must be an ISO 8601 date-time.", ErrorCode.INVALID_INPUT) from None
    return moment.replace(tzinfo=UTC) if moment.tzinfo is None else moment.astimezone(UTC)


def _is_newer(attrs: dict[str, Any], since: datetime | None) -> bool:
    if since is None:
        return True
    moment = posted(attrs.get("posted_dt"))
    return moment is not None and moment > since


@tool(
    name="search_projects",
    title="Search projects",
    access="read",
    confirm=False,
    description="Open projects buyers posted, newest first, with budget, category, proposals and the brief's start.",
    details=(
        "Returns open projects from the same search as the Jobs page on PeoplePerHour, newest first. Filter by "
        "keyword, top category, or posting time: with since, only projects posted after it come back, so an agent "
        "polling for new work reads only what arrived since its last check. Times are UTC. budget.type is "
        "fixed_price or hourly (then the amount is per hour), in the buyer's currency. freelancer_country is set "
        "when only freelancers from that country may send a proposal. get_project returns the full brief. Pass "
        "next_cursor back as cursor for the next page; it is null when nothing more matches. With since, one call "
        "scans at most 200 of the newest projects, so a page can hold fewer than limit and still have a next_cursor."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/search",
    example_response=EXAMPLE_RESPONSE,
)
async def search_projects(ctx: ToolContext, args: dict[str, Any]) -> Any:
    size = limit(args, 20, 50)
    page, offset = _position(args.get("cursor"))
    since = _since(args.get("since"))
    query: dict[str, Any] = {"sort": "latest", "withoutFacets": 1, "page[size]": PAGE_SIZE}
    if keyword := (args.get("query") or "").strip():
        query["filter[keyword]"] = keyword
    if category := args.get("category"):
        query["filter[category]"] = CATEGORIES[category]

    projects: list[dict[str, Any]] = []
    for _ in range(MAX_PAGES if since else 2):
        body = await v2(ctx, "GET", "/projects/listAll", params={**query, "page[number]": page})
        data = [item for item in (body.get("data") or []) if isinstance(item, dict)]
        for index in range(offset, len(data)):
            attrs = data[index].get("attributes") or {}
            if not _is_newer(attrs, since):
                continue
            if len(projects) == size:
                return {"projects": projects, "next_cursor": f"{page}.{index}"}
            projects.append({**project_row(attrs), "excerpt": excerpt(attrs.get("proj_desc"))})
        last_page = not (body.get("links") or {}).get("next") or len(data) < PAGE_SIZE
        # `latest` is not strictly by posted_dt, so only a whole page with nothing newer ends a `since` scan.
        nothing_newer = since is not None and not any(_is_newer(i.get("attributes") or {}, since) for i in data)
        if last_page or nothing_newer:
            return {"projects": projects, "next_cursor": None}
        page, offset = page + 1, 0
        if len(projects) == size:
            break
    return {"projects": projects, "next_cursor": str(page)}
