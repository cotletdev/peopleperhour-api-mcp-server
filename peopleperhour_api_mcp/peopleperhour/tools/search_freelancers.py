"""Search freelancers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import limit, page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._people import freelancer_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

# The filter values of /hire-freelancers , in the viewer's currency for the rate.
RATES = ["*-10", "10-30", "30-50", "50-*"]
SORTS = ["most-relevant", "cert", "latest", "rate", "rating", "most-sales"]
MIN_RATING = {"60": "60-*", "70": "70-*", "80": "80-*"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Skill or keywords, e.g. logo design."},
        "hourly_rate": {
            "type": "string",
            "enum": RATES,
            "description": "Hourly rate band in your account currency: *-10, 10-30, 30-50 or 50-*.",
        },
        "min_rating": {
            "type": "string",
            "enum": sorted(MIN_RATING),
            "description": "Only freelancers rated at least this percent.",
        },
        "top_certified": {"type": "boolean", "description": "Only freelancers with a CERT level."},
        "sort": {"type": "string", "enum": SORTS, "description": "Order. Default: most-relevant."},
        "limit": {"type": "integer", "description": "1 to 50. Default: 20. Keep it the same across pages."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "freelancers": [
        {
            "freelancer_id": "1204511",
            "name": "Laura M.",
            "url": "https://www.peopleperhour.com/freelancer/design/laura-brand-and-logo-designer-qxzvwy",
            "job_title": "Brand and logo designer",
            "city": "Bristol",
            "country": "United Kingdom",
            "hourly_rate": {"amount": 30, "currency": "GBP"},
            "certification": "TOP",
            "verified": True,
            "rating_percent": 99,
            "reviews": 412,
            "projects_completed": 530,
            "buyers_worked_with": 380,
            "response_time": "within a few hours",
            "last_project_at": "2026-10-20T14:02:11Z",
            "member_since": "2016-03-02",
            "skills": ["Logo design", "Brand design"],
            "languages": ["English"],
            "portfolio_items": 24,
            "about": "I design logos and brand identities for small businesses…",
        }
    ],
    "total": 2798,
    "next_cursor": "2",
}


@tool(
    name="search_freelancers",
    title="Search freelancers",
    access="read",
    confirm=False,
    description="Freelancers by skill or keyword, with rate, rating, reviews, completed projects and skills.",
    details=(
        "Returns freelancers from the same search as Hire freelancers on PeoplePerHour: short name, profile URL, "
        "job title, location, hourly rate in the freelancer's currency, CERT level, rating in percent, review and "
        "project counts, skills and the start of their About text. hourly_rate filters in your account currency. "
        "get_freelancer returns the full profile. Pass next_cursor back as cursor with the same limit; it is null "
        "on the last page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /freelancers/search",
    example_response=EXAMPLE_RESPONSE,
)
async def search_freelancers(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page, size = page_cursor(args.get("cursor")), limit(args, 20, 50)
    query: dict[str, Any] = {
        "include": "skillTags,sellerStats",
        "withoutFacets": 1,
        "page[number]": page,
        "page[size]": size,
        "sort": args.get("sort") or "most-relevant",
    }
    if keyword := (args.get("query") or "").strip():
        query["filter[keyword]"] = keyword
    if rate := args.get("hourly_rate"):
        query["filter[hourlyRate]"] = rate
    if rating := args.get("min_rating"):
        query["filter[rating]"] = MIN_RATING[rating]
    if args.get("top_certified"):
        query["filter[cert]"] = "1-*"
    body = await v2(ctx, "GET", "/sellers/listAll", params=query)
    rows = [freelancer_row(item.get("attributes") or {}, about_excerpt=True) for item in items(body)]
    total = (body.get("meta") or {}).get("total-items")
    return {
        "freelancers": rows,
        "total": total if isinstance(total, int) else len(rows),
        "next_cursor": next_page(body, page) if rows else None,
    }
