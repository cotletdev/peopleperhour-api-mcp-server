"""List categories."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import items, v2

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

CURRENCIES = ["GBP", "USD", "EUR"]
# The answer is about 240 KB and changes rarely: one copy a day for every account.
CACHE_KEY = "categories"
CACHE_S = 86400
# `medianBudgets` keys: freelancer level (below 4, 4, 5, Top CERT) and the overall average.
_LEVELS = {"<4": "below_level_4", "4": "level_4", "5": "level_5", "top": "top", "avg": "average"}

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "currency": {
            "type": "string",
            "enum": CURRENCIES,
            "description": "Currency of the median budgets. Default: GBP.",
        }
    },
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "categories": [
        {
            "category": "writing-translation",
            "name": "Writing & Translation",
            "subcategories": [
                {
                    "subcategory_id": "449",
                    "name": "Translation",
                    "slug": "translators",
                    "median_budget": {
                        "currency": "GBP",
                        "fixed": {"below_level_4": 50, "level_4": 60, "level_5": 70, "top": 90, "average": 99},
                        "hourly": {"below_level_4": 13, "level_4": 14, "level_5": 16, "top": 19, "average": 21},
                    },
                }
            ],
        }
    ]
}


def _budget(meta: Any, currency: str) -> dict[str, Any] | None:
    found = ((meta or {}).get("medianBudgets") or {}).get(currency) if isinstance(meta, dict) else None
    if not isinstance(found, dict):
        return None
    return {
        "currency": currency,
        **{kind: {_LEVELS.get(k, k): v for k, v in (found.get(kind) or {}).items()} for kind in ("fixed", "hourly")},
    }


async def _raw(ctx: ToolContext) -> dict[str, Any]:
    if cached := await ctx.cache_get(CACHE_KEY):
        return json.loads(cached)
    body = await v2(ctx, "GET", "/categories", params={"include": "subcategories"})
    # Only what the tool reads, so the cached copy stays small.
    slim = {
        "categories": [item.get("attributes") or {} for item in items(body)],
        "subcategories": [
            {**(item.get("attributes") or {}), "meta": item.get("meta")}
            for item in (body.get("included") or [])
            if isinstance(item, dict) and item.get("type") == "subcategories"
        ],
    }
    if slim["categories"]:
        await ctx.cache_set(CACHE_KEY, json.dumps(slim), CACHE_S)
    return slim


@tool(
    name="list_categories",
    title="List categories",
    access="read",
    confirm=False,
    credits=20,
    description="The 10 project categories with their subcategories and typical budgets per freelancer level.",
    details=(
        "Returns PeoplePerHour's project categories and their subcategories. category is the slug search_projects "
        "and save_search take. median_budget is PeoplePerHour's median project budget in the subcategory, fixed "
        "price and hourly, by freelancer level (below level 4, level 4, level 5, Top CERT) and on average, in the "
        "currency asked for: a guide when pricing a proposal or a project."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /categories",
    example_response=EXAMPLE_RESPONSE,
)
async def list_categories(ctx: ToolContext, args: dict[str, Any]) -> Any:
    currency = args.get("currency") or "GBP"
    raw = await _raw(ctx)
    subs: dict[str, list[dict[str, Any]]] = {}
    for sub in raw.get("subcategories") or []:
        subs.setdefault(str(sub.get("cate_id")), []).append(
            {
                "subcategory_id": str(sub.get("subcate_id") or ""),
                "name": sub.get("subcate_name") or "",
                "slug": sub.get("slug") or None,
                "median_budget": _budget(sub.get("meta"), currency),
            }
        )
    return {
        "categories": [
            {
                "category": cat.get("slug") or "",
                "name": cat.get("cate_name") or "",
                "subcategories": subs.get(str(cat.get("cate_id")), []),
            }
            for cat in raw.get("categories") or []
        ]
    }
