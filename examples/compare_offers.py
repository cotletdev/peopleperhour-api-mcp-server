#!/usr/bin/env python3
"""Compare PeoplePerHour Offers before buying: price, delivery days, add-ons and what each seller needs from you.

python compare_offers.py "wordpress speed" --price-range 50-100 --top 3
"""

import argparse

from peopleperhour_api_mcp.scripting import call, run, write_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("query", help="Keywords, e.g. wordpress speed")
    parser.add_argument("--price-range", choices=["0-19", "20-50", "50-100", "100-*"], help="Band, account currency")
    parser.add_argument("--sort", default="most-sales", help="featured, trending, most-sales, hourlie-rating, ...")
    parser.add_argument("--top", type=int, default=3, help="How many Offers to read (default 3)")
    parser.add_argument("--out", help="Save to .csv or .json instead of printing")
    args = parser.parse_args()

    found = call(
        "search_offers", {"query": args.query, "price_range": args.price_range, "sort": args.sort, "limit": args.top}
    )
    rows = []
    for o in found["offers"][: args.top]:
        offer = call("get_offer", {"offer_id": o["offer_id"]})
        rows.append(
            {
                "title": offer["title"],
                "url": offer["url"],
                "price": offer["price"],
                "delivery_days": offer["delivery_days"],
                "sales": offer["sales"],
                "rating_percent": offer["rating_percent"],
                "seller": offer["freelancer"]["name"],
                "response_time": offer["response_time"],
                "add_ons": [f"{a['description']} (+{a['price']}, +{a['extra_days']} days)" for a in offer["add_ons"]],
                "needs_from_you": offer["requirements"],
            }
        )
    write_rows(rows, args.out)


if __name__ == "__main__":
    run(main)
