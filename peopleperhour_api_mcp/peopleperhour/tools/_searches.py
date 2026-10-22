"""Saved project searches (`memberSavedSearch`) as list_saved_searches and save_search return them."""

from __future__ import annotations

from typing import Any

from peopleperhour_api_mcp.peopleperhour.tools._projects import CATEGORIES, iso

ALERTS = ["Never", "Daily", "Instantly"]
EXPERIENCE = {"entry": 1, "intermediate": 2, "expert": 3}
PRICING = ["fixed_price", "hourly"]
LOCATIONS = ["remote", "onsite"]
# projectType values of the Jobs filter: "-hasProposals" is "with no proposals yet".
PROJECT_TYPES = {
    "urgent": "urgent",
    "no_proposals": "-hasProposals",
    "pre_funded": "preFunded",
    "featured": "featured",
    "high_value": "highValue",
}
_SLUGS = {cate_id: slug for slug, cate_id in CATEGORIES.items()}


def _listed(value: Any) -> list[Any]:
    if value in (None, "", []):
        return []
    return value if isinstance(value, list) else [value]


def search_row(item: dict[str, Any]) -> dict[str, Any]:
    """One saved search; `filters` uses the argument names of save_search."""
    attrs = item.get("attributes") or {}
    raw = (item.get("meta") or {}).get("projectListingFilters") or attrs.get("projectListingFilters") or {}
    raw = raw if isinstance(raw, dict) else {}
    levels = {str(n): name for name, n in EXPERIENCE.items()}
    types = {value: name for name, value in PROJECT_TYPES.items()}
    filters = {
        "query": raw.get("keyword") or None,
        "category": _SLUGS.get(str(raw.get("category") or "")),
        "experience_level": next((levels[str(v)] for v in _listed(raw.get("experience")) if str(v) in levels), None),
        "pricing": raw.get("pricing") or None,
        "location": raw.get("location") or None,
        "project_types": [types[str(v)] for v in _listed(raw.get("projectType")) if str(v) in types],
    }
    return {
        "saved_search_id": str(item.get("id") or attrs.get("id") or ""),
        "title": attrs.get("title") or "",
        "alert": attrs.get("alert") or None,
        "filters": filters,
        "created_at": iso(attrs.get("created_at")),
    }
