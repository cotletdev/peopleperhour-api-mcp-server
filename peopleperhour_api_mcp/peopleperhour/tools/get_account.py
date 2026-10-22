"""Get account."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import included, items, me, v2

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "member_id": "13900001",
    "name": "Alex P.",
    "email": "alex@example.com",
    "type": "buyer",
    "location": "Oxford, GB",
    "currency": "GBP",
    "profile_url": "https://www.peopleperhour.com/freelancer/alex-zxnxjy",
    "member_since": "2026-10-22",
    "new_messages": 0,
    "buyer_stats": {
        "projects_total": 0,
        "projects_listed": 0,
        "projects_completed": 0,
        "freelancers_worked_with": 0,
        "jobs_awarded_ratio": 0,
        "response_time": "instantly",
    },
    "favourites": {"offers": 0, "freelancers": 0, "watched_projects": 1},
}

_FAVOURITES = {"hourlies": "offers", "people": "freelancers", "jobs": "watched_projects"}


def _count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


async def favourite_counts(ctx: ToolContext, member_id: str) -> dict[str, int]:
    """Counts of favourite Offers, favourite freelancers and watched projects (`/members/{me}/favorites`)."""
    body = await v2(ctx, "GET", f"/members/{member_id}/favorites")
    counts = dict.fromkeys(_FAVOURITES.values(), 0)
    for item in items(body):
        if (name := _FAVOURITES.get(str(item.get("id")))) is not None:
            counts[name] = _count((item.get("attributes") or {}).get("count"))
    return counts


@tool(
    name="get_account",
    title="Get account",
    access="read",
    confirm=False,
    description="The signed-in PeoplePerHour account: name, type, buyer stats, unread messages and favourite counts.",
    details=(
        "Returns the account the tools act as: member id, first name and initial, email, account type (buyer or "
        "seller), location, currency, profile URL, unread messages, buyer stats (projects posted, listed and "
        "completed, freelancers worked with, share of projects awarded, response time) and how many Offers, "
        "freelancers and projects it keeps as favourites or watches."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /account",
    example_response=EXAMPLE_RESPONSE,
)
async def get_account(ctx: ToolContext, args: dict[str, Any]) -> Any:
    member = await me(ctx)
    member_id = str(member["id"])
    body = await v2(ctx, "GET", f"/members/{member_id}", params={"include": "buyerStats"})
    data = body.get("data") if isinstance(body, dict) else None
    public = (data.get("attributes") or {}) if isinstance(data, dict) else {}
    stats = next(iter(included(body, "memberBuyerStats")), {})
    initial = (member.get("lname") or "")[:1]
    return {
        "member_id": member_id,
        "name": f"{member.get('fname') or ''} {initial + '.' if initial else ''}".strip() or None,
        "email": member.get("email") or None,
        "type": member.get("memberType") or None,
        "location": member.get("location") or None,
        "currency": member.get("userCurrency") or public.get("currency") or None,
        "profile_url": member.get("profile_url") or public.get("url") or None,
        "member_since": member.get("registration_date") or public.get("reg_dt") or None,
        "new_messages": _count(public.get("new_messages")),
        "buyer_stats": {
            "projects_total": _count(stats.get("projects_total")),
            "projects_listed": _count(stats.get("projects_listed")),
            "projects_completed": _count(stats.get("projects_completed")),
            "freelancers_worked_with": _count(stats.get("sellers_worked")),
            "jobs_awarded_ratio": stats.get("jobs_awarded_ratio") or 0,
            "response_time": stats.get("response_time") or None,
        },
        "favourites": await favourite_counts(ctx, member_id),
    }
