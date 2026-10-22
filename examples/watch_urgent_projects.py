#!/usr/bin/env python3
"""Check for urgent PeoplePerHour projects in a category that still have few proposals. Run it hourly from cron.

python watch_urgent_projects.py --category design --max-proposals 5 --state urgent_state.json

With --state the script remembers when it last ran and reads only projects posted after that.
"""

import argparse
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from peopleperhour_api_mcp.scripting import paginate, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--category", required=True, help="Top category, e.g. design or writing-translation")
    parser.add_argument("--max-proposals", type=int, default=5, help="Report only below this many (default 5)")
    parser.add_argument("--hours", type=int, default=1, help="Look back N hours when there is no state (default 1)")
    parser.add_argument("--state", help="JSON file that keeps the time of the last check")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    now = datetime.now(UTC)
    since = now - timedelta(hours=args.hours)
    state = Path(args.state) if args.state else None
    if state and state.exists():
        since = datetime.fromisoformat(json.loads(state.read_text())["last_check"])

    params = {"category": args.category, "since": since.isoformat(), "limit": 50}
    rows = [
        {k: p[k] for k in ("title", "url", "budget", "proposals", "posted_at")}
        for p in paginate("search_projects", params, "projects")
        if p["urgent"] and p["proposals"] < args.max_proposals
    ]
    write_rows(rows, args.out)
    if state:
        state.write_text(json.dumps({"last_check": now.isoformat()}))


if __name__ == "__main__":
    run(main)
