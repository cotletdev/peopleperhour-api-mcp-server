"""Shapes of PeoplePerHour freelancers (`sellers`, `members`) and Offers (`hourlies`) as the tools return them."""

from __future__ import annotations

import re
from typing import Any

from peopleperhour_api_mcp.peopleperhour.tools._projects import excerpt, iso

_ID = re.compile(r"(\d+)$")


def number(value: Any) -> float | int | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return int(result) if result.is_integer() else round(result, 2)


def percent(value: Any) -> int | None:
    """`feedback_rating` is a 0-1 share (string or float); the page shows it as a percent."""
    share = number(value)
    return round(share * 100) if share is not None else None


def skills(raw: Any) -> list[str]:
    """`skillTags` is `{tag_id: label}`."""
    return [str(label) for label in raw.values() if label] if isinstance(raw, dict) else []


def languages(raw: Any) -> list[str]:
    return [str(item.get("label")) for item in raw or [] if isinstance(item, dict) and item.get("label")]


def certification(value: Any) -> str | None:
    """`cert` is `TOP`, a level number, or "0" for none."""
    text = str(value or "").strip()
    return None if text in ("", "0") else text


def freelancer_short(attrs: Any) -> dict[str, Any] | None:
    """The freelancer as an Offer shows them: short name only, never the full name."""
    if not isinstance(attrs, dict) or not attrs.get("mem_id"):
        return None
    return {
        "freelancer_id": str(attrs.get("mem_id")),
        "name": attrs.get("shortName") or attrs.get("public_name") or None,
        "url": attrs.get("url") or None,
        "country": attrs.get("country") or None,
        "certification": certification(attrs.get("cert")),
    }


def freelancer_row(attrs: dict[str, Any], *, about_excerpt: bool) -> dict[str, Any]:
    """The fields search_freelancers and get_freelancer share."""
    stats = attrs.get("seller_stats")
    stats = stats if isinstance(stats, dict) else {}
    about = attrs.get("about") or ""
    return {
        "freelancer_id": str(attrs.get("mem_id") or ""),
        "name": attrs.get("shortName") or attrs.get("public_name") or "",
        "url": attrs.get("url") or None,
        "job_title": (attrs.get("job_title") or "").strip() or None,
        "city": attrs.get("city") or None,
        "country": attrs.get("country") or None,
        "hourly_rate": {"amount": number(attrs.get("hourly_rate")), "currency": attrs.get("currency") or None},
        "certification": certification(attrs.get("cert")),
        "verified": str(attrs.get("verified")) == "1",
        "rating_percent": percent(stats.get("feedback_rating")),
        "reviews": int(number(stats.get("reviews")) or 0),
        "projects_completed": int(number(stats.get("projects_completed")) or 0),
        "buyers_worked_with": int(number(stats.get("buyers_worked")) or 0),
        "response_time": stats.get("response_time") or None,
        "last_project_at": iso(stats.get("last_project")),
        "member_since": attrs.get("reg_dt") or None,
        "skills": skills(attrs.get("skillTags")),
        "languages": languages(attrs.get("spoken_languages")),
        "portfolio_items": int(number(attrs.get("countPortfolioItems")) or 0),
        "about": excerpt(about) if about_excerpt else about,
    }


def offer_id(value: Any) -> str | None:
    """The number from an id or from an Offer URL (`/hourlie/<title>/252788`)."""
    text = str(value or "").strip().split("?")[0].split("#")[0].rstrip("/")
    match = _ID.search(text)
    return match.group(1) if match else None


def offer_row(attrs: dict[str, Any]) -> dict[str, Any]:
    """The fields search_offers and get_offer share."""
    category = attrs.get("category")
    category = category if isinstance(category, dict) else {}
    tags = attrs.get("tagList")
    tags = tags if isinstance(tags, list) else []
    return {
        "offer_id": str(attrs.get("hourlie_id") or ""),
        "title": attrs.get("title") or "",
        "url": attrs.get("url") or None,
        "price": {"amount": number(attrs.get("price")), "currency": attrs.get("currency") or None},
        "delivery_days": attrs.get("availabilityDeliveryDays"),
        "sales": int(number(attrs.get("sales")) or 0),
        "rating_percent": number(attrs.get("rating")),
        "category": category.get("cate_name") or None,
        "subcategory": category.get("subcate_name") or None,
        "tags": [str(t.get("label")) for t in tags if isinstance(t, dict) and t.get("label")],
        "summary": attrs.get("short_description") or "",
        "created_at": iso(attrs.get("created_at")),
        "freelancer": freelancer_short(attrs.get("freelancer")),
    }
