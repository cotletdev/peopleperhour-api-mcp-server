"""Get freelancer."""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import WWW, included, v2
from peopleperhour_api_mcp.peopleperhour.tools._people import freelancer_row
from peopleperhour_api_mcp.peopleperhour.tools._projects import iso

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

NOT_FOUND = "PeoplePerHour has no freelancer with this freelancer_id."
PORTFOLIO_MAX = 30
# The profile page's own config carries the member id: '\x2Fmember\x2Fstar\x3Fmem_id\x3D670675'.
_MEM_ID = re.compile(r"mem_id\\x3D(\d+)")
_PROJECT = re.compile(r'<a class="job" title="([^"]*)" href="([^"]+)"')
_TIME = re.compile(r'<time class="message-time" title="([^"]+)"')
_NAME = re.compile(r'<h6 class="participant-name[^"]*">(.*?)</h6>', re.DOTALL)
_PLACE = re.compile(r'<div class="participant-location">(.*?)</div>', re.DOTALL)
_RATING = re.compile(r'name="rating" value="(\d)"')
_TEXT = re.compile(r"</header>\s*<p>(.*?)</p>", re.DOTALL)
_REPLY = re.compile(r'class="feedback-reply[^"]*">.*?<p>(.*?)</p>', re.DOTALL)
_TAG = re.compile(r"<[^>]+>")
_UK = ZoneInfo("Europe/London")

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "freelancer_id": {
            "type": "string",
            "description": "freelancer_id from search_freelancers or an Offer, or the freelancer's profile URL.",
        }
    },
    "required": ["freelancer_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "freelancer_id": "1204511",
    "name": "Laura M.",
    "url": "https://www.peopleperhour.com/freelancer/design/laura-brand-and-logo-designer-qxzvwy",
    "job_title": "Brand and logo designer",
    "city": "Bristol",
    "country": "United Kingdom",
    "hourly_rate": {"amount": 30, "currency": "GBP"},
    "certification": "TOP",
    "verified": True,
    "rating_percent": 99,
    "reviews": 412,
    "projects_completed": 530,
    "buyers_worked_with": 380,
    "response_time": "within a few hours",
    "last_project_at": "2026-10-20T14:02:11Z",
    "member_since": "2016-03-02",
    "skills": ["Logo design", "Brand design"],
    "languages": ["English"],
    "portfolio_items": 24,
    "about": "I design logos and brand identities for small businesses.",
    "portfolio": [
        {
            "title": "Coffee shop logo",
            "type": "image",
            "image": "https://dw3i9sxi97owk.cloudfront.net/uploads/portfolioItems/8f2c.jpg",
            "thumbnail": "https://dw3i9sxi97owk.cloudfront.net/uploads/thumbs/8f2c_210x150.jpg",
            "uploaded_at": "2024-05-11T09:30:00Z",
        }
    ],
    "recent_reviews": [
        {
            "project": "Logo for a bakery",
            "project_url": "https://www.peopleperhour.com/freelance-jobs/design/logo-design/logo-for-a-bakery-4526001",
            "reviewer": "Tom B.",
            "reviewer_location": "Leeds, GB",
            "rating": 5,
            "text": "Quick, clear and the logo is exactly what we wanted.",
            "reply": None,
            "reviewed_at": "2026-10-16T12:32:00Z",
        }
    ],
}


def _member_id(value: Any) -> tuple[str | None, str | None]:
    """(id, None) for a number, (None, profile URL) for a link."""
    text = str(value or "").strip()
    if text.isdigit():
        return text, None
    if text.startswith(("http://", "https://", "www.", "peopleperhour.com")) and "/freelancer/" in text:
        url = text if text.startswith("http") else f"https://{text}"
        return None, url.replace("http://", "https://").split("?")[0].split("#")[0]
    raise ToolError("freelancer_id must be a number from search_freelancers or a profile URL.", ErrorCode.INVALID_INPUT)


def _clean(fragment: str) -> str:
    return " ".join(html.unescape(_TAG.sub(" ", fragment)).split())


def _uk_time(value: str) -> str | None:
    """'Fri, 16 Oct 2026  at 1:32pm' in UK time to ISO 8601 UTC."""
    try:
        # The page prints UK wall time with no zone, so the zone is attached to the parsed time.
        moment = datetime.strptime(" ".join(value.split()), "%a, %d %b %Y at %I:%M%p").replace(tzinfo=_UK)
    except ValueError:
        return None
    return moment.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _reviews(page: str) -> list[dict[str, Any]]:
    """The reviews under each project on the profile page (`li.item.participant.feedback`), first page only."""
    found: list[dict[str, Any]] = []
    blocks = page.split('<div class="project-list-item')[1:]
    for block in blocks:
        project = _PROJECT.search(block)
        for item in block.split('<li class="item participant feedback')[1:]:
            when, name, place = _TIME.search(item), _NAME.search(item), _PLACE.search(item)
            rating, text, reply = _RATING.search(item), _TEXT.search(item), _REPLY.search(item)
            found.append(
                {
                    "project": html.unescape(project.group(1)) if project else None,
                    "project_url": project.group(2) if project else None,
                    "reviewer": _clean(name.group(1)) if name else None,
                    "reviewer_location": (_clean(place.group(1)) or None) if place else None,
                    "rating": int(rating.group(1)) if rating else None,
                    "text": _clean(text.group(1)) if text else "",
                    "reply": _clean(reply.group(1)) if reply else None,
                    "reviewed_at": _uk_time(when.group(1)) if when else None,
                }
            )
    return found


async def _profile_page(ctx: ToolContext, url: str) -> str:
    response = await ctx.call("GET", url, headers={"accept": "text/html", "referer": f"{WWW}/"})
    if response.status == 404:
        raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)
    if response.status != 200:
        raise ToolError("PeoplePerHour could not answer this request. Try again later.", ErrorCode.TARGET_ERROR)
    return response.text


@tool(
    name="get_freelancer",
    title="Get freelancer",
    access="read",
    confirm=False,
    description="A freelancer's public profile: rate, stats, skills, portfolio and the latest reviews on the page.",
    details=(
        "Returns a freelancer's public profile: short name, job title, location, hourly rate, CERT level, rating in "
        "percent, review and project counts, skills, languages, full About text, up to 30 portfolio items, and the "
        "reviews the profile page shows (usually the latest few, with the project they came from). reviews is the "
        "total count; PeoplePerHour does not let older reviews be paged, so only recent_reviews come with text. "
        "Times are UTC. Pass a freelancer_id from search_freelancers or an Offer, or the profile URL."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /freelancers/{freelancer_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_freelancer(ctx: ToolContext, args: dict[str, Any]) -> Any:
    member, url = _member_id(args.get("freelancer_id"))
    page = await _profile_page(ctx, url) if url else None
    if page is not None:
        found = _MEM_ID.search(page)
        if not found:
            raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)
        member = found.group(1)
    body = await v2(
        ctx, "GET", f"/members/{member}", params={"include": "skillTags,sellerStats,portfolio"}, not_found=NOT_FOUND
    )
    data = body.get("data") if isinstance(body, dict) else None
    attrs = (data.get("attributes") or {}) if isinstance(data, dict) else {}
    if not attrs.get("mem_id"):
        raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)
    if page is None and attrs.get("url"):
        page = await _profile_page(ctx, str(attrs["url"]))
    portfolio = [
        {
            "title": None if (item.get("title") or "-").strip() == "-" else item.get("title"),
            "type": item.get("item_type") or None,
            "image": item.get("file_path") or None,
            "thumbnail": item.get("thumbnail") or None,
            "uploaded_at": iso(item.get("date_uploaded")),
        }
        for item in included(body, "memberPortfolio")[:PORTFOLIO_MAX]
    ]
    return {
        **freelancer_row(attrs, about_excerpt=False),
        "portfolio": portfolio,
        "recent_reviews": _reviews(page or ""),
    }
