"""Shapes of PeoplePerHour's project records (`/v2/projects`) as search_projects and get_project return them."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError

# The 10 top categories of GET /v2/categories (22.10.2026): PeoplePerHour's slug (as in project URLs) -> cate_id.
CATEGORIES = {
    "artificial-intelligence": "48",
    "business": "45",
    "design": "27",
    "digital-marketing": "44",
    "marketing-branding-sales": "43",
    "music-audio": "46",
    "social-media": "37",
    "technology-programming": "42",
    "video-photography": "47",
    "writing-translation": "41",
}
# budget_bracket, the experience level the buyer picked (meta.filters.experience of listAll).
_EXPERIENCE = {1: "entry", 2: "intermediate", 3: "expert"}
UPLOADS = "https://dw3i9sxi97owk.cloudfront.net/uploads/"
EXCERPT_CHARS = 300


def posted(value: Any) -> datetime | None:
    """`posted_dt` and `expiry_dt` are "YYYY-MM-DD HH:MM:SS" in UTC (checked against the page's "posted ... ago")."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip()).replace(tzinfo=UTC)
    except ValueError:
        return None


def iso(value: Any) -> str | None:
    moment = posted(value)
    return moment.isoformat().replace("+00:00", "Z") if moment else None


def _number(value: Any) -> float | int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number.is_integer() else number


def _experience(value: Any) -> str | None:
    try:
        return _EXPERIENCE.get(int(value))
    except (TypeError, ValueError):
        return None


def _country_only(attrs: dict[str, Any]) -> str | None:
    """`where_can_bid` is "ALL" or the one country (ISO code) whose freelancers may send proposals."""
    value = attrs.get("where_can_bid")
    return value if isinstance(value, str) and value and value.upper() != "ALL" else None


def project_row(attrs: dict[str, Any]) -> dict[str, Any]:
    """The fields search_projects and get_project share."""
    category = attrs.get("category") or {}
    sub = attrs.get("sub_category") or {}
    return {
        "project_id": str(attrs.get("proj_id") or ""),
        "title": attrs.get("title") or "",
        "url": attrs.get("url") or None,
        "budget": {
            "amount": _number(attrs.get("budget")),
            "currency": attrs.get("currency") or None,
            "type": attrs.get("project_type") or None,
        },
        "category": category.get("cate_name") or None,
        "subcategory": sub.get("subcate_name") or None,
        "experience_level": _experience(attrs.get("budget_bracket")),
        "location_type": attrs.get("location_type") or None,
        "freelancer_country": _country_only(attrs),
        "urgent": bool(attrs.get("isUrgent")),
        "featured": bool(attrs.get("isFeatured")),
        "proposals": attrs.get("proposalCount") if isinstance(attrs.get("proposalCount"), int) else 0,
        "posted_at": iso(attrs.get("posted_dt")),
        "expires_at": iso(attrs.get("expiry_dt")),
    }


def excerpt(text: Any) -> str:
    """The start of the brief, on one line, for a list item."""
    flat = " ".join(str(text or "").split())
    return flat if len(flat) <= EXCERPT_CHARS else flat[: EXCERPT_CHARS - 1].rstrip() + "…"


def attachments(attrs: dict[str, Any]) -> list[str]:
    """Public links of the files the buyer attached (`project_attachment1..3`, empty slots skipped)."""
    raw = attrs.get("project_attachments") or {}
    paths = [raw[key] for key in sorted(raw) if isinstance(raw[key], str) and raw[key].strip()]
    return [UPLOADS + quote(path.strip(), safe="/") for path in paths]


def project_id(value: Any) -> str:
    """The number from an id or from a project URL (`.../website-design-4527860`)."""
    text = str(value or "").strip().split("?")[0].split("#")[0].rstrip("/")
    match = re.search(r"(\d+)$", text)
    if not match:
        raise ToolError("project_id must come from search_projects or be a project URL.", ErrorCode.INVALID_INPUT)
    return match.group(1)
