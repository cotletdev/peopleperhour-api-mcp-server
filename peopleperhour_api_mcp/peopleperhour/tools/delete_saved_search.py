"""Delete saved search."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import v2

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

NOT_FOUND = "This account has no saved search with this saved_search_id."

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {"saved_search_id": {"type": "string", "description": "saved_search_id from list_saved_searches."}},
    "required": ["saved_search_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"saved_search_id": "861203", "deleted": True}


@tool(
    name="delete_saved_search",
    title="Delete saved search",
    access="write",
    confirm=False,
    description="Delete one of this account's saved project searches and its email alert.",
    details="Deletes the saved search from the signed-in account; its email alert stops with it.",
    input_schema=INPUT_SCHEMA,
    route="DELETE /saved-searches/{saved_search_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def delete_saved_search(ctx: ToolContext, args: dict[str, Any]) -> Any:
    search_id = str(args.get("saved_search_id") or "").strip()
    if not search_id.isdigit():
        raise ToolError("saved_search_id must come from list_saved_searches.", ErrorCode.INVALID_INPUT)
    await v2(ctx, "DELETE", f"/memberSavedSearches/{search_id}", not_found=NOT_FOUND)
    return {"saved_search_id": search_id, "deleted": True}
