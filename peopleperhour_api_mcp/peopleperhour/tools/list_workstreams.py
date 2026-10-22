"""List WorkStreams."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.helpers import page_cursor
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import WWW, items, next_page, v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import iso

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"cursor": {"type": "string", "description": "next_cursor from the previous call."}},
    "required": [],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "workstreams": [
        {
            "workstream_id": "7712034",
            "title": "Logo for a coffee shop",
            "url": "https://www.peopleperhour.com/stream/view?id=7712034",
            "unread_messages": 1,
            "last_message": {"text": "First concepts are attached.", "sent_at": "2026-10-22T17:40:02Z"},
        }
    ],
    "next_cursor": None,
}


def _included(body: Any) -> dict[tuple[str, str], dict[str, Any]]:
    found = body.get("included") if isinstance(body, dict) else None
    return {
        (str(item.get("type")), str(item.get("id"))): item.get("attributes") or {}
        for item in found or []
        if isinstance(item, dict)
    }


def _row(item: dict[str, Any], extra: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    # Fields read from the WorkStreams menu's code (title, url, unread_messages, lastMessage txt and create_dt);
    # not yet seen on a real account.
    attrs = item.get("attributes") or {}
    link = (((item.get("relationships") or {}).get("lastMessage") or {}).get("data")) or {}
    message = extra.get((str(link.get("type") or "streamMessages"), str(link.get("id")))) if link else None
    url = attrs.get("url") or None
    unread = attrs.get("unread_messages")
    return {
        "workstream_id": str(item.get("id") or ""),
        "title": attrs.get("title") or "",
        "url": f"{WWW}{url}" if isinstance(url, str) and url.startswith("/") else url,
        "unread_messages": unread if isinstance(unread, int) else int(bool(unread)),
        "last_message": {"text": message.get("txt") or "", "sent_at": iso(message.get("create_dt"))}
        if message
        else None,
    }


@tool(
    name="list_workstreams",
    title="List WorkStreams",
    access="read",
    confirm=False,
    credits=20,
    description="This account's WorkStreams (conversations with hired freelancers) with the last message.",
    details=(
        "Returns the WorkStreams of the signed-in account, the conversation PeoplePerHour opens for each hire: "
        "title, link, unread message count and the last message with its time. It reads, never sends: replying "
        "is done on PeoplePerHour. Pass next_cursor back as cursor; it is null on the last page."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /workstreams",
    example_response=EXAMPLE_RESPONSE,
)
async def list_workstreams(ctx: ToolContext, args: dict[str, Any]) -> Any:
    page = page_cursor(args.get("cursor"))
    query = {"include": "lastMessage,client,freelancer", "page[number]": page}
    body = await v2(ctx, "GET", "/streams/list", params=query)
    extra = _included(body)
    rows = [_row(item, extra) for item in items(body)]
    return {"workstreams": rows, "next_cursor": next_page(body, page) if rows else None}
