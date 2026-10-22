#!/usr/bin/env python3
"""Save a PeoplePerHour project search with an email alert, then list all saved searches.

python save_project_alert.py "Urgent design" --category design --pricing fixed_price --type urgent --alert Daily
python save_project_alert.py --list

PeoplePerHour allows 10 saved searches per account. Delete one with
`peopleperhour-mcp call delete_saved_search saved_search_id=<id>`.
"""

import argparse

from peopleperhour_api_mcp.scripting import call, paginate, run, write_rows

TYPES = ["urgent", "no_proposals", "pre_funded", "featured", "high_value"]


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("title", nargs="?", help="Name of the new saved search")
    parser.add_argument("--query", help="Keywords")
    parser.add_argument("--category", help="Top category, e.g. design or writing-translation")
    parser.add_argument("--experience", choices=["entry", "intermediate", "expert"], help="Level the buyer asked for")
    parser.add_argument("--pricing", choices=["fixed_price", "hourly"])
    parser.add_argument("--type", action="append", choices=TYPES, dest="types", help="Project type, repeatable")
    parser.add_argument(
        "--alert", choices=["Never", "Daily", "Instantly"], default="Daily", help="Email (default Daily)"
    )
    parser.add_argument("--list", action="store_true", help="Only list the saved searches")
    parser.add_argument("--out", help="Save the list to .csv or .json instead of printing")
    args = parser.parse_args()

    if not args.list:
        if not args.title:
            parser.error("give a title, or --list")
        saved = call(
            "save_search",
            {
                "title": args.title,
                "alert": args.alert,
                "query": args.query,
                "category": args.category,
                "experience_level": args.experience,
                "pricing": args.pricing,
                "project_types": args.types,
            },
        )
        print(f"Saved search {saved['saved_search_id']}: {saved['title']}, alert {saved['alert']}")
    write_rows(list(paginate("list_saved_searches", {}, "saved_searches")), args.out)


if __name__ == "__main__":
    run(main)
