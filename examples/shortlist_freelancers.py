#!/usr/bin/env python3
"""Shortlist PeoplePerHour freelancers for a job: search, then read each profile and its latest reviews.

python shortlist_freelancers.py "logo design" --hourly-rate 10-30 --min-rating 80 --top 5
"""

import argparse

from peopleperhour_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("query", help="Skill or keywords, e.g. logo design")
    parser.add_argument("--hourly-rate", choices=["*-10", "10-30", "30-50", "50-*"], help="Rate band, account currency")
    parser.add_argument("--min-rating", choices=["60", "70", "80"], help="Only freelancers rated at least this percent")
    parser.add_argument("--top", type=int, default=5, help="How many profiles to read (default 5)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    found = call(
        "search_freelancers",
        {"query": args.query, "hourly_rate": args.hourly_rate, "min_rating": args.min_rating, "limit": args.top},
    )
    rows = []
    for f in found["freelancers"][: args.top]:
        profile = call("get_freelancer", {"freelancer_id": f["freelancer_id"]})
        reviews = profile["recent_reviews"]
        rows.append(
            {
                "name": profile["name"],
                "url": profile["url"],
                "job_title": profile["job_title"],
                "hourly_rate": profile["hourly_rate"],
                "rating_percent": profile["rating_percent"],
                "reviews": profile["reviews"],
                "projects_completed": profile["projects_completed"],
                "response_time": profile["response_time"],
                "last_project_at": profile["last_project_at"],
                "portfolio_items": profile["portfolio_items"],
                "recent_average": round(sum(r["rating"] for r in reviews) / len(reviews), 2) if reviews else None,
                "latest_review": reviews[0]["text"] if reviews else None,
            }
        )
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
