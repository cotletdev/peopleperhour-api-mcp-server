"""Who is signed in: PeoplePerHour's own member record (GET /v2/members/me), for "Signed in as ..."."""

from __future__ import annotations

from typing import TYPE_CHECKING

from peopleperhour_api_mcp.core.errors import AuthExpiredError
from peopleperhour_api_mcp.peopleperhour.client import v2

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext


async def whoami(ctx: ToolContext) -> str | None:
    """None only when PeoplePerHour says signed out; any other failure raises (detection tries again later).

    Signed out, /v2/members/me still answers 200, with `shared` only and no `member`.
    """
    try:
        body = await v2(ctx, "GET", "/members/me")
    except AuthExpiredError:
        return None
    member = body.get("member") if isinstance(body, dict) else None
    if not isinstance(member, dict) or not member.get("id"):
        return None
    name = f"{member.get('fname') or ''} {member.get('lname') or ''}".strip()
    email = member.get("email")
    return f"{name} ({email})" if name and email else name or email or None
