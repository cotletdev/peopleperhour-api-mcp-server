"""List notifications."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import WWW, items, me, v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import iso

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {"type": "object", "properties": {}, "required": [], "additionalProperties": False}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "notifications": [
        {
            "notification_id": "90211457",
            "text": "You have a new proposal on Logo for a coffee shop",
            "url": "https://www.peopleperhour.com/job/4527990/proposals",
            "read": False,
            "created_at": "2026-10-22T18:02:11Z",
        }
    ],
    "unread": {"notifications": 1, "proposals": 1, "messages": 0},
}


def _count(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _row(item: dict[str, Any]) -> dict[str, Any]:
    # Item shape read from the bell menu's code (text, date, is_read, url); not yet seen on a real account.
    attrs = item.get("attributes")
    attrs = attrs if isinstance(attrs, dict) else item
    url = attrs.get("url") or None
    return {
        "notification_id": str(item.get("id") or attrs.get("id") or ""),
        "text": attrs.get("text") or attrs.get("message") or "",
        "url": f"{WWW}{url}" if isinstance(url, str) and url.startswith("/") else url,
        "read": bool(attrs.get("is_read")),
        "created_at": iso(attrs.get("date") or attrs.get("created_at")) or attrs.get("date") or None,
    }


@tool(
    name="list_notifications",
    title="List notifications",
    access="read",
    confirm=False,
    credits=20,
    description="The latest notifications of this account (proposals, messages, project updates) and unread counts.",
    details=(
        "Returns the notifications under the bell on PeoplePerHour, newest first: text, link, whether it was read "
        "and when it came. unread counts unread notifications, proposals and WorkStream messages. Reading does not "
        "mark anything as read."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /notifications",
    example_response=EXAMPLE_RESPONSE,
)
async def list_notifications(ctx: ToolContext, args: dict[str, Any]) -> Any:
    member = await me(ctx)
    body = await v2(ctx, "GET", "/notifications/top")
    counts = await v2(ctx, "GET", f"/members/{member['id']}/notificationsCountForMobileOnly")
    unread = {str(item.get("id")): _count((item.get("attributes") or {}).get("count")) for item in items(counts)}
    return {
        "notifications": [_row(item) for item in items(body)],
        "unread": {
            "notifications": unread.get("unread_notifications", 0),
            "proposals": unread.get("unread_proposals", 0),
            "messages": unread.get("unread_messages", 0),
        },
    }
