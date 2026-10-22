"""Watch project."""

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
        "project_id": {"type": "string", "description": "project_id from search_projects, or the project's URL."}
    },
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {"project_id": "4527860", "watching": True}


@tool(
    name="watch_project",
    title="Watch project",
    access="write",
    confirm=False,
    description="Add a project to this account's watchlist (Favourite Jobs) to come back to it later.",
    details=(
        "Adds the project to the watchlist of the signed-in account, the heart on the project page. The buyer is "
        "not notified. Watching a project already on the list changes nothing. list_watchlist reads the list and "
        "unwatch_project takes it off."
    ),
    input_schema=INPUT_SCHEMA,
    route="PUT /projects/{project_id}/watch",
    example_response=EXAMPLE_RESPONSE,
)
async def watch_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    pid = project_id(args.get("project_id"))
    await v2(ctx, "PUT", f"/projects/{pid}/star", not_found=NOT_FOUND)
    return {"project_id": pid, "watching": True}
