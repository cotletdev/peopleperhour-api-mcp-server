"""PeoplePerHour's web API on www.peopleperhour.com, recorded on the dev account (22.10.2026).

The site is a React app on legacy `/site/*` pages; its JSON API lives on the same host: `/v1/user/*` for sign-in
and the account, `/v2/*` for the rest. Every call carries a fixed `app_id`/`app_key` query pair from the page
code (one pair for `/v1/user`, another for `/v2`), not a secret of the account. The session is the httpOnly
cookie `api` (about 100 days with "Remember me"), next to `PHPSESSID` and `YII_CSRF_TOKEN`; no header is needed.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import AuthExpiredError, ErrorCode, ToolError

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

WWW = "https://www.peopleperhour.com"
SESSION_COOKIE = "api"
# The page code's own pairs; the API answers 401 to a call without them.
V1_KEYS = {"app_id": "0dd8b0ea", "app_key": "d9cc1b8dcab4249a0f321b9c411bf037"}
V2_KEYS = {"app_id": "23h2j27d", "app_key": "48c4a5fb862168be0a029894f4eca210"}
_PHP_TEXT = re.compile(r"\d+ => '([^']+)'")
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
    """One `/v2` call (`path` after `/v2`, e.g. `/members/me`); returns the JSON body, None for an empty one.

    200, 201 (a watch) and 204 (a deleted saved search) succeed. A 404 raises `not_found` when given; a 400 raises
    PeoplePerHour's own validation text. A bare 403 never gets here: the joining layer ends it as `target_blocked`.
    """
    response = await ctx.call(
        method, f"{WWW}/v2{path}", params={**V2_KEYS, **(params or {})}, headers=_HEADERS, **kwargs
    )
    if response.status == 404 and not_found:
        raise ToolError(not_found, ErrorCode.TARGET_ERROR)
    if response.status == 400 and (problems := _validation(response.text)):
        raise ToolError(problems, ErrorCode.TARGET_ERROR)
    if response.status not in (200, 201, 204):
        raise ToolError("PeoplePerHour could not answer this request. Try again later.", ErrorCode.TARGET_ERROR)
    return response.json() if response.text.strip() else None


def _validation(text: str) -> str:
    """`{errors: [{meta: {attribute}, detail}]}` of a 400 as one line, "" when the body is something else."""
    try:
        errors = json.loads(text).get("errors")
    except (ValueError, AttributeError):
        return ""
    if not isinstance(errors, list):
        return ""
    details = [str(e.get("detail")).strip() for e in errors if isinstance(e, dict) and e.get("detail")]
    # Some details are a PHP array dump: "array ( 'experienceLevel' => array ( 0 => 'Experience Level is not ...' ) )".
    return " ".join(" ".join(_PHP_TEXT.findall(d)) or d for d in details)


async def me(ctx: ToolContext) -> dict[str, Any]:
    """The signed-in member of `/members/me` (`id`, `fname`, `lname`, `email`, `memberType`, ...)."""
    body = await v2(ctx, "GET", "/members/me")
    member = body.get("member") if isinstance(body, dict) else None
    if not isinstance(member, dict) or not member.get("id"):
        raise AuthExpiredError("The app signed this account out.")
    return member


def next_page(body: Any, page: int) -> str | None:
    """The cursor of the page after `page`, None on the last one (`links.next` is absent there)."""
    links = body.get("links") if isinstance(body, dict) else None
    return str(page + 1) if isinstance(links, dict) and links.get("next") else None


def items(body: Any) -> list[dict[str, Any]]:
    """`data[]` of a JSON:API answer, only the objects."""
    data = body.get("data") if isinstance(body, dict) else None
    return [item for item in data if isinstance(item, dict)] if isinstance(data, list) else []


def included(body: Any, kind: str) -> list[dict[str, Any]]:
    """`attributes` of every `included[]` record of one type."""
    found = body.get("included") if isinstance(body, dict) else None
    return [item.get("attributes") or {} for item in found or [] if isinstance(item, dict) and item.get("type") == kind]
