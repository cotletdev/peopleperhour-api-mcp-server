"""Get Offer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import included, v2
from peopleperhour_api_mcp.peopleperhour.tools._people import number, offer_id, offer_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

NOT_FOUND = "PeoplePerHour has no Offer with this offer_id."
INCLUDE = "attachments,hourlieTags,prices,addons"

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "offer_id": {"type": "string", "description": "offer_id from search_offers, or the Offer's page URL."}
    },
    "required": ["offer_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
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
    "description": "A logo that fits your brand, with three concepts to choose from.",
    "requirements": "Your colours, any designs you like and a few lines about your business.",
    "response_time": "within a few hours",
    "ratings": {"5": 1265, "4": 63, "3": 27, "2": 15, "1": 23},
    "prices": [{"amount": 75, "currency": "GBP"}, {"amount": 87, "currency": "EUR"}],
    "add_ons": [{"description": "Two more concepts", "price": 30, "extra_days": 1}],
    "images": ["https://dw3i9sxi97owk.cloudfront.net/uploads/hourliesAttachments/thumbs/550x413/2021/03/99a0.jpg"],
}


@tool(
    name="get_offer",
    title="Get Offer",
    access="read",
    confirm=False,
    description="One Offer with its full description, what the seller needs from you, prices, add-ons and images.",
    details=(
        "Returns one Offer as its page shows it: title, price in your account currency and in each currency the "
        "seller set, delivery days, sales, rating in percent with the count per star, full description, what the "
        "buyer must send, add-ons with their price and extra days, image links and the freelancer who sells it. "
        "Pass an offer_id from search_offers or the Offer's URL."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /offers/{offer_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_offer(ctx: ToolContext, args: dict[str, Any]) -> Any:
    oid = offer_id(args.get("offer_id"))
    if not oid:
        raise ToolError("offer_id must come from search_offers or be an Offer URL.", ErrorCode.INVALID_INPUT)
    body = await v2(ctx, "GET", f"/hourlies/{oid}", params={"include": INCLUDE}, not_found=NOT_FOUND)
    data = body.get("data") if isinstance(body, dict) else None
    attrs = (data.get("attributes") or {}) if isinstance(data, dict) else {}
    if not attrs.get("hourlie_id"):
        raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)
    stars = ((data or {}).get("meta") or {}).get("ratings") or []
    images = [
        (item.get("image_urls") or {}).get("large")
        for item in included(body, "hourlieAttachments")
        if isinstance(item.get("image_urls"), dict)
    ]
    return {
        **offer_row(attrs),
        "description": attrs.get("description") or "",
        "requirements": attrs.get("requirements") or "",
        "response_time": attrs.get("response_time") or None,
        "ratings": {str(s.get("stars")): s.get("count") for s in stars if isinstance(s, dict) and s.get("stars")},
        "prices": [
            {"amount": number(p.get("price")), "currency": p.get("currency")}
            for p in included(body, "hourliePrice")
            if p.get("currency")
        ],
        "add_ons": [
            {
                "description": a.get("description") or "",
                "price": number(a.get("price")),
                "extra_days": a.get("duration"),
            }
            for a in included(body, "hourlieAddons")
        ],
        "images": [url for url in images if url],
    }
