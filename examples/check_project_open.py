#!/usr/bin/env python3
"""Check whether PeoplePerHour projects are still open and how many proposals each has now.

python check_project_open.py 4527712 4527860
"""

import argparse

from peopleperhour_api_mcp.core.errors import ToolError
from peopleperhour_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("projects", nargs="+", help="project_id values or project page URLs")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = []
    for project in args.projects:
        try:
            p = call("get_project", {"project_id": project})
        except ToolError as err:
            # Private, removed or unknown projects get a row of their own instead of stopping the run.
            rows.append({"project": project, "open": False, "error": str(err)})
            continue
        rows.append(
            {
                "project": p["project_id"],
                "title": p["title"],
                "open": p["open"],
                "status": p["status"],
                "proposals": p["proposals"],
                "expires_at": p["expires_at"],
            }
        )
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
