"""PeoplePerHour's web API on www.peopleperhour.com, recorded on the dev account (22.10.2026).

The site is a React app on legacy `/site/*` pages; its JSON API lives on the same host: `/v1/user/*` for sign-in
and the account, `/v2/*` for the rest. Every call carries a fixed `app_id`/`app_key` query pair from the page
code (one pair for `/v1/user`, another for `/v2`), not a secret of the account. The session is the httpOnly
cookie `api` (about 100 days with "Remember me"), next to `PHPSESSID` and `YII_CSRF_TOKEN`; no header is needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

WWW = "https://www.peopleperhour.com"
SESSION_COOKIE = "api"
# The page code's own pairs; the API answers 401 to a call without them.
V1_KEYS = {"app_id": "0dd8b0ea", "app_key": "d9cc1b8dcab4249a0f321b9c411bf037"}
V2_KEYS = {"app_id": "23h2j27d", "app_key": "48c4a5fb862168be0a029894f4eca210"}
_HEADERS = {"accept": "application/json, text/plain, */*", "referer": f"{WWW}/"}


async def v2(
    ctx: ToolContext,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    not_found: str | None = None,
    **kwargs: Any,
) -> Any:
    """One `/v2` call (`path` after `/v2`, e.g. `/members/me`); returns the JSON body.

    A 404 raises `not_found` when given. A bare 403 never gets here: the joining layer ends it as `target_blocked`.
    """
    response = await ctx.call(
        method, f"{WWW}/v2{path}", params={**V2_KEYS, **(params or {})}, headers=_HEADERS, **kwargs
    )
    if response.status == 404 and not_found:
        raise ToolError(not_found, ErrorCode.TARGET_ERROR)
    if response.status != 200:
        raise ToolError("PeoplePerHour could not answer this request. Try again later.", ErrorCode.TARGET_ERROR)
    return response.json()
