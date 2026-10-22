#!/usr/bin/env python3
"""Find new PeoplePerHour projects for your skills: drop those under your budget floor or with too many proposals,
then read the full brief of the rest.

python find_new_projects.py --query "web design" --query webflow --hours 24 --min-budget 200 --max-proposals 15
"""

import argparse
from datetime import UTC, datetime, timedelta
from typing import Any

from peopleperhour_api_mcp.scripting import call, paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--query", action="append", required=True, help="A skill keyword; repeat for more")
    parser.add_argument("--category", help="Only this top category, e.g. design or technology-programming")
    parser.add_argument("--hours", type=int, default=24, help="Projects posted in the last N hours (default 24)")
    parser.add_argument("--min-budget", type=float, default=0, help="Skip budgets below this, in the buyer's currency")
    parser.add_argument("--max-proposals", type=int, help="Skip projects with more proposals than this")
    parser.add_argument("--hourly-rate", type=float, help="With hourly projects, the floor is this rate instead")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    since = (datetime.now(UTC) - timedelta(hours=args.hours)).strftime("%Y-%m-%dT%H:%M:%SZ")
    found: dict[str, dict[str, Any]] = {}
    for query in args.query:
        params = {"query": query, "category": args.category, "since": since, "limit": 50}
        for project in paginate("search_projects", params, "projects"):
            found.setdefault(project["project_id"], {**project, "matched": []})["matched"].append(query)

    rows = []
    for project in found.values():
        budget = project["budget"]
        floor = args.hourly_rate if budget["type"] == "hourly" and args.hourly_rate else args.min_budget
        if (budget["amount"] or 0) < floor:
            continue
        if args.max_proposals is not None and project["proposals"] > args.max_proposals:
            continue
        full = call("get_project", {"project_id": project["project_id"]})
        if not full["open"]:
            continue
        rows.append(
            {
                "title": full["title"],
                "url": full["url"],
                "budget": budget["amount"],
                "currency": budget["currency"],
                "type": budget["type"],
                "proposals": full["proposals"],
                "freelancer_country": full["freelancer_country"],
                "posted_at": full["posted_at"],
                "matched": ", ".join(project["matched"]),
                "questions": full["interview_questions"],
                "attachments": full["attachments"],
                "brief": full["brief"],
            }
        )
    rows.sort(key=lambda r: r["proposals"])
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
