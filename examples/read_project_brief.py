#!/usr/bin/env python3
"""Read one PeoplePerHour project before you write a proposal: brief, attached files, the buyer's questions,
proposal count and the 80% price floor.

python read_project_brief.py 4527712
python read_project_brief.py https://www.peopleperhour.com/freelance-jobs/design/web-design/website-design-4527860
"""

import argparse

from peopleperhour_api_mcp.scripting import call, run


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("project", help="project_id from search_projects, or the project's page URL")
    args = parser.parse_args()

    p = call("get_project", {"project_id": args.project})
    budget = p["budget"]
    state = "open" if p["open"] else f"closed ({p['status']})"
    print(f"{p['title']}\n{p['url']}\n")
    print(f"{state}, {budget['amount']} {budget['currency']} {budget['type']}, {p['proposals']} proposals")
    print(f"posted {p['posted_at']}, expires {p['expires_at']}")
    if budget["amount"]:
        # PeoplePerHour wants a proposal of at least 80% of the budget the buyer gave.
        print(f"lowest proposal PeoplePerHour accepts: {round(budget['amount'] * 0.8, 2)} {budget['currency']}")
    if p["freelancer_country"]:
        print(f"only freelancers from {p['freelancer_country']} may send a proposal")
    if p["client"]:
        c = p["client"]
        print(f"buyer: {c['name']}, {c['city'] or '?'}, {c['country'] or '?'}, member since {c['member_since']}")
    print(f"\n{p['brief']}\n")
    for question in p["interview_questions"]:
        print(f"question: {question}")
    for link in p["attachments"]:
        print(f"file: {link}")


if __name__ == "__main__":
    run(main)
