"""Get project."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from peopleperhour_api_mcp.core.errors import ErrorCode, ToolError
from peopleperhour_api_mcp.core.tools import tool
from peopleperhour_api_mcp.peopleperhour.client import v2
from peopleperhour_api_mcp.peopleperhour.tools._projects import attachments, project_id, project_row

if TYPE_CHECKING:
    from peopleperhour_api_mcp.core.context import ToolContext

# What the project page asks for, plus the onsite place and the one country allowed to bid (seen 22.10.2026).
INCLUDE = "interviewQuestions,projectAttachment,projectsOnsiteInfo,locations,onsiteLocation,remoteCountry"
NOT_FOUND = "PeoplePerHour has no project with this project_id."
NOT_PUBLIC = "This project is not public on PeoplePerHour (private, removed or under review)."

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "project_id": {
            "type": "string",
            "description": "project_id from search_projects, or the project's page URL.",
        }
    },
    "required": ["project_id"],
    "additionalProperties": False,
}

EXAMPLE_RESPONSE: dict[str, Any] = {
    "project_id": "4527712",
    "title": "Photographer and videographer for a product shoot",
    "url": "https://www.peopleperhour.com/freelance-jobs/video-photography/photography/photographer-4527712",
    "budget": {"amount": 450, "currency": "GBP", "type": "fixed_price"},
    "category": "Video, Photo & Image",
    "subcategory": "Photography",
    "experience_level": "intermediate",
    "location_type": "remote_country",
    "freelancer_country": "GB",
    "urgent": False,
    "featured": False,
    "proposals": 6,
    "posted_at": "2026-10-21T12:43:02Z",
    "expires_at": "2026-11-20T12:43:02Z",
    "status": "open",
    "open": True,
    "brief": "We need photos and short videos of our new product range.\nThe brief is attached.",
    "onsite_location": None,
    "attachments": ["https://dw3i9sxi97owk.cloudfront.net/uploads/jobAttachments/GiNc_brief%20v2.docx"],
    "interview_questions": ["Why do you like this project?", "What are your greatest strengths?"],
    "client": {
        "name": "Josh S.",
        "city": "Birmingham",
        "country": "United Kingdom",
        "member_since": "2013-08-15",
        "url": "https://www.peopleperhour.com/freelancer/social-media/josh-s-qazyxq",
    },
}


def _included(body: dict[str, Any], kind: str, item_id: Any = None) -> list[dict[str, Any]]:
    return [
        item.get("attributes") or {}
        for item in body.get("included") or []
        if isinstance(item, dict) and item.get("type") == kind and (item_id is None or item.get("id") == item_id)
    ]


def _onsite(body: dict[str, Any], data: dict[str, Any]) -> dict[str, Any] | None:
    """Where an onsite project is done: the `locations` record its `onsiteLocation` relationship points to."""
    if (data.get("attributes") or {}).get("location_type") != "onsite":
        return None
    link = ((data.get("relationships") or {}).get("onsiteLocation") or {}).get("data") or {}
    place = next(iter(_included(body, "locations", link.get("id"))), {}) if link.get("id") else {}
    return {
        "city": place.get("city") or None,
        "region": place.get("admin_area") or None,
        "country": place.get("country") or None,
    }


def _client(raw: Any) -> dict[str, Any] | None:
    """The buyer as the project page shows them; never their full name, rate or about text."""
    if not isinstance(raw, dict):
        return None
    return {
        "name": raw.get("shortName") or raw.get("public_name") or None,
        "city": raw.get("city") or None,
        "country": raw.get("country") or None,
        "member_since": raw.get("reg_dt") or None,
        "url": raw.get("url") or None,
    }


@tool(
    name="get_project",
    title="Get project",
    access="read",
    confirm=False,
    description="One project's full brief with budget, attachments, interview questions, buyer and proposal count.",
    details=(
        "Returns one project as its public page shows it: the buyer's full brief, budget, category, experience "
        "level, where it is done, links to the files the buyer attached, the questions the buyer asks in a "
        "proposal, how many proposals it has and whether it is still open. client is the buyer's public profile. "
        "Times are UTC. Pass a project_id from search_projects or the project's URL."
    ),
    input_schema=INPUT_SCHEMA,
    route="GET /projects/{project_id}",
    example_response=EXAMPLE_RESPONSE,
)
async def get_project(ctx: ToolContext, args: dict[str, Any]) -> Any:
    pid = project_id(args.get("project_id"))
    try:
        body = await v2(ctx, "GET", f"/projects/{pid}", params={"include": INCLUDE}, not_found=NOT_FOUND)
    except ToolError as exc:
        # PeoplePerHour answers a bare 403 for private, removed or moderated projects; the session is fine.
        if exc.code == ErrorCode.TARGET_BLOCKED:
            raise ToolError(NOT_PUBLIC, ErrorCode.TARGET_ERROR) from None
        raise
    data = body.get("data") if isinstance(body, dict) else None
    data = data if isinstance(data, dict) else {}
    attrs = data.get("attributes") or {}
    if not attrs.get("proj_id"):
        raise ToolError(NOT_FOUND, ErrorCode.TARGET_ERROR)
    questions = next((q.get("questions") for q in _included(body, "interviewQuestions") if q.get("questions")), None)
    return {
        **project_row(attrs),
        "status": attrs.get("item_state") or None,
        "open": bool(attrs.get("open")),
        "brief": attrs.get("proj_desc") or "",
        "onsite_location": _onsite(body, data),
        "attachments": attachments(attrs),
        "interview_questions": [str(q) for q in questions] if isinstance(questions, list) else [],
        "client": _client(attrs.get("client")),
    }
