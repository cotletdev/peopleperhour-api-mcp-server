"""Search Offers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import limit, page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._people import offer_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

# The filter values of /services ; prices in the viewer's currency.
PRICES = ["0-19", "20-50", "50-100", "100-*"]
SORTS = ["featured", "trending", "most-sales", "hourlie-rating", "price-asc", "price-desc"]

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "Keywords, e.g. logo design."},
        "price_range": {
            "type": "string",
            "enum": PRICES,
            "description": "Price band in your account currency: 0-19, 20-50, 50-100 or 100-*.",
        },
        "sort": {"type": "string", "enum": SORTS, "description": "Order. Default: featured."},
        "limit": {"type": "integer", "description": "1 to 50. Default: 20. Keep it the same across pages."},
        "cursor": {"type": "string", "description": "next_cursor from the previous call."},
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "offers": [
        {
            "offer_id": "252788",
            "title": "Design a logo with 3 initial concepts",
            "url": "https://www.peopleperhour.com/hourlie/design-a-logo-with-3-initial-concepts/252788",
            "price": {"amount": 75, "currency": "GBP"},
            "delivery_days": 1,
            "sales": 2212,
            "rating_percent": 96,
            "category": "Design",
            "subcategory": "Logo Design",
            "tags": ["Logo design", "Vector logo"],
            "summary": "Your logo pack includes print, web and source files.",
            "created_at": "2015-12-19T20:26:26Z",
            "freelancer": {
                "freelancer_id": "1013296",
                "name": "Sam K.",
                "url": "https://www.peopleperhour.com/freelancer/design/sam-branding-and-logo-zazxyn",
                "country": "United Kingdom",
                "certification": "TOP",
            },
        }
    ],
    "total": 2596,
    "next_cursor": "2",
}


@tool(
    name="search_offers",
    title="Search Offers",
    access="read",
    confirm=False,
    description="Fixed-price Offers freelancers sell, by keyword or price, with sales, rating and seller.",
    details=(
        "Returns Offers (fixed-price services, once called Hourlies) from the same search as the Offers page on "
        "PeoplePerHour: title, price in your account currency, delivery days, sales, rating in percent, category, "
        "tags and the freelancer who sells it. get_offer returns the description, add-ons and images. Pass "
        "next_cursor back as cursor with the same limit; it is null on the last page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /offers/search",
    example_response=EXAMPLE_RESPONSE,
)
async def search_offers(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page, size = page_cursor(args.get("cursor")), limit(args, 20, 50)
    query: dict[str, Any] = {
        "include": "freelancer",
        "page[number]": page,
        "page[size]": size,
        "sort": args.get("sort") or "featured",
    }
    # `filter[keyword]` is ignored here; Offers search by `search_term`.
    if keyword := (args.get("query") or "").strip():
        query["filter[search_term]"] = keyword
    if price := args.get("price_range"):
        query["filter[priceRange]"] = price
    body = await v2(ctx, "GET", "/hourlies/listAll", params=query)
    rows = [offer_row(item.get("attributes") or {}) for item in items(body)]
    total = (body.get("meta") or {}).get("total-items")
    return {
        "offers": rows,
        "total": total if isinstance(total, int) else len(rows),
        "next_cursor": next_page(body, page) if rows else None,
    }
