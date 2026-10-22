#!/usr/bin/env python3
"""What PeoplePerHour buyers usually pay in a category: median fixed and hourly budgets per freelancer level.

python median_budgets.py translation --currency USD
python median_budgets.py --out budgets.csv
"""

import argparse

from peopleperhour_api_mcp.scripting import call, run, write_rows

LEVELS = ("below_level_4", "level_4", "level_5", "top", "average")


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("match", nargs="?", default="", help="Words in a category or subcategory name (default all)")
    parser.add_argument("--currency", choices=["GBP", "USD", "EUR"], default="GBP")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    rows = []
    for cat in call("list_categories", {"currency": args.currency})["categories"]:
        for sub in cat["subcategories"]:
            if args.match.lower() not in f"{cat['name']} {sub['name']}".lower():
                continue
            median = sub.get("median_budget") or {}
            row = {"category": cat["name"], "subcategory": sub["name"], "currency": median.get("currency")}
            for kind in ("fixed", "hourly"):
                for level in LEVELS:
                    row[f"{kind}_{level}"] = (median.get(kind) or {}).get(level)
            rows.append(row)
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
