#!/usr/bin/env python3
"""Morning check for a PeoplePerHour buyer: open projects with proposal counts, unread notifications and WorkStreams.

python buyer_daily_digest.py
python buyer_daily_digest.py --out digest.json
"""

import argparse
import json
from pathlib import Path

from peopleperhour_api_mcp.scripting import call, paginate, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--status", default="open", help="Project state to list (default open)")
    parser.add_argument("--out", help="Save to a .json file instead of printing")
    args = parser.parse_args()

    projects = [
        {k: p[k] for k in ("title", "url", "budget", "proposals", "expires_at")}
        for p in paginate("list_my_projects", {"status": args.status}, "projects")
    ]
    bell = call("list_notifications")
    workstreams = [w for w in paginate("list_workstreams", {}, "workstreams") if w["unread_messages"]]
    digest = {
        "projects": projects,
        "unread": bell["unread"],
        "unread_notifications": [n for n in bell["notifications"] if not n["read"]],
        "workstreams_with_unread": workstreams,
    }
    text = json.dumps(digest, indent=2, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    run(main)
