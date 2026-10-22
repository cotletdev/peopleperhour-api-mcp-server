"""Unwatch project."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import project_id

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

NOT_FOUND = "PeoplePerHour has no project with this project_id."

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {"type": "string", "description": "project_id from list_watchlist, or the project's URL."}
    },
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"project_id": "4527860", "watching": False}


@tool(
    name="unwatch_project",
    title="Unwatch project",
    access="write",
    confirm=False,
    description="Take a project off this account's watchlist.",
    details="Removes the project from the watchlist of the signed-in account. Nobody else is told.",
    input_schema=INPUT_SCHEMA,
    route="DELETE /projects/{project_id}/watch",
    example_response=EXAMPLE_RESPONSE,
)
async def unwatch_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    pid = project_id(args.get("project_id"))
    await v2(ctx, "DELETE", f"/projects/{pid}/star", not_found=NOT_FOUND)
    return {"project_id": pid, "watching": False}
