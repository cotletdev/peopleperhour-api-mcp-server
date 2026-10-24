# PeoplePerHour API and MCP server, self-hosted

<!-- mcp-name: dev.cotlet/peopleperhour -->

A **PeoplePerHour API** and a **PeoplePerHour MCP server** you run on your own computer, in Python, on the session of your own Google Chrome. The same 17 PeoplePerHour tools we run in production at [Cotlet](https://cotlet.dev/integrations/peopleperhour-api-mcp-server): search open projects and read full briefs, search freelancers and Offers and read profiles with recent reviews, keep a project watchlist and saved searches with email alerts, see median budgets per category, and read your own posted projects, notifications and WorkStreams.

PeoplePerHour has no public API and no official MCP server. This repo gives you both:

- **MCP server** for Claude Code, Claude Desktop, Cursor, Codex and any MCP client, over stdio or HTTP. [Setup](#mcp-server)
- **REST API** on `http://127.0.0.1:8787/api/v1/peopleperhour`, with OpenAPI docs at `/docs`. [Setup](#rest-api)
- **Python**: `call("search_projects", query="web design")`, plus 9 ready scripts in [`examples/`](examples/).

13 tools read. The other 4 change only your own watchlist and saved searches. Nothing here sends a proposal or a message, posts a project, buys an Offer or pays, and no Proposal credit is spent.

It is for technical people who want to run it themselves, **for noncommercial use only** ([license](#license)). If you want it running 24/7 on a server, kept working when PeoplePerHour changes its site, for a team or a business, use the [hosted version at cotlet.dev](https://cotlet.dev/integrations/peopleperhour-api-mcp-server).

[![PeoplePerHour MCP server](https://img.shields.io/badge/PeoplePerHour%20MCP-17%20tools-6d4aef)](#all-17-tools)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-141318)](#requirements)
[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial-141318)](LICENSE)
[![MCP Badge](https://lobehub.com/badge/mcp/cotletdev-peopleperhour-api-mcp-server)](https://lobehub.com/mcp/cotletdev-peopleperhour-api-mcp-server)

```bash
git clone https://github.com/cotletdev/peopleperhour-api-mcp-server.git && cd peopleperhour-api-mcp-server
python3 -m venv .venv && . .venv/bin/activate && pip install -e .
peopleperhour-mcp connect                          # reads your PeoplePerHour session from Chrome
peopleperhour-mcp call search_projects query="web design" limit=5
claude mcp add peopleperhour -- "$PWD/.venv/bin/peopleperhour-mcp" mcp
```

## Contents

- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Install](#install)
- [Connect your Chrome](#connect-your-chrome)
- [MCP server](#mcp-server)
- [REST API](#rest-api)
- [Python and the example scripts](#python-and-the-example-scripts)
- [All 17 tools](#all-17-tools)
- [Configuration](#configuration)
- [Security and your PeoplePerHour account](#security-and-your-peopleperhour-account)
- [Errors](#errors)
- [Self-hosted or hosted](#self-hosted-or-hosted)
- [FAQ](#faq)
- [License](#license)

## How it works

```text
AI agent (MCP) / script (REST, Python) ──▶ peopleperhour-mcp on your computer ──your cookies──▶ www.peopleperhour.com
                                                    ▲
                      peopleperhour-mcp connect ────┘ reads them once from your Chrome (DevTools Protocol)
```

1. You sign in to PeoplePerHour in your own Chrome, the way you always do. Tick **Remember me**.
2. `peopleperhour-mcp connect` attaches to that Chrome through the Chrome DevTools Protocol, reads the peopleperhour.com cookies and saves them to `~/.config/peopleperhour-api-mcp/session.json`, readable by your user only. It never sees or stores your password.
3. Every tool call is a request to the JSON API the PeoplePerHour site itself calls (`www.peopleperhour.com/v2/...`) with those cookies, sent with [curl_cffi](https://github.com/lexiforest/curl_cffi), which copies Chrome's TLS fingerprint. No headless browser runs.

The session lives in the `api` cookie, about 100 days after a sign-in with Remember me. When PeoplePerHour signs you out, the server reads the cookies from Chrome again, if Chrome is open with remote debugging on.

## Requirements

- Python 3.11 or newer.
- Google Chrome 144 or newer, signed in to PeoplePerHour. Any Chrome or Chromium works with a [debugging port](#option-b-a-chrome-with-a-debugging-port).
- macOS, Linux or Windows.
- Any PeoplePerHour account. A free buyer account is enough for all 17 tools.

## Install

```bash
git clone https://github.com/cotletdev/peopleperhour-api-mcp-server.git
cd peopleperhour-api-mcp-server
python3 -m venv .venv
. .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e .
peopleperhour-mcp --version
```

With [uv](https://docs.astral.sh/uv/): `uv venv && uv pip install -e .`, then `uv run peopleperhour-mcp ...`.

Setting it up with an AI agent (Claude Code, Codex, Cursor)? Open it in this folder and ask it to set up the repo: [`AGENTS.md`](AGENTS.md) tells it every step, and it asks you only for the steps in Chrome.

To update: `git pull && pip install -e .`. We copy every change of the hosted PeoplePerHour tools into this repo.

## Connect your Chrome

### Option A: your everyday Chrome (recommended)

1. Open `chrome://inspect/#remote-debugging` in Chrome and switch **remote debugging** on. Chrome then accepts DevTools connections from programs on this computer, and asks you before each one.
2. Make sure you are signed in at [peopleperhour.com](https://www.peopleperhour.com/site/login).
3. Run:

   ```bash
   peopleperhour-mcp connect
   ```

4. Chrome asks whether to allow the connection. Click **Allow**.

```text
Saved 9 PeoplePerHour cookies to /Users/you/.config/peopleperhour-api-mcp/session.json
Signed in to PeoplePerHour as Maya Reed (maya@yourname.com)
```

You can switch remote debugging off again afterwards. Leave it on if you want the server to pick up a new session by itself after PeoplePerHour signs you out.

`connect` looks for Chrome's `DevToolsActivePort` file in the default profile folder. For Chrome Beta, Canary or a custom profile folder, pass `--profile-dir "<folder>"`.

### Option B: a Chrome with a debugging port

Chrome does not open a debugging port on your default profile, so start a separate one, sign in to PeoplePerHour there once, and connect to it:

```bash
# macOS
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-pph"
# Linux
google-chrome --remote-debugging-port=9222 --user-data-dir="$HOME/.chrome-pph"
# Windows
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --user-data-dir="%USERPROFILE%\.chrome-pph"

peopleperhour-mcp connect --cdp http://127.0.0.1:9222
```

`--cdp` also takes a `ws://` DevTools URL, for example of a Chrome on another machine reached over an SSH tunnel.

### Option C: paste the cookie by hand

For a server with no Chrome: in Chrome open DevTools on peopleperhour.com, **Application > Cookies > https://www.peopleperhour.com**, copy the value of `api`, then:

```bash
peopleperhour-mcp connect --token          # paste it, input is hidden
# or, without a session file:
export PEOPLEPERHOUR_AUTH_TOKEN=...
```

A pasted token is not refreshed on its own. Paste a new one when PeoplePerHour signs you out.

Check the session at any time:

```bash
peopleperhour-mcp status
```

## MCP server

The MCP server lists all 17 tools with their input schemas and a description written for agents. The 13 read tools are marked read-only; `--read-only` hides the 4 that change your watchlist and saved searches.

### Claude Code

```bash
claude mcp add peopleperhour -- /path/to/peopleperhour-api-mcp-server/.venv/bin/peopleperhour-mcp mcp
```

### Claude Desktop

`~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "peopleperhour": {
      "command": "/path/to/peopleperhour-api-mcp-server/.venv/bin/peopleperhour-mcp",
      "args": ["mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`, the same block as Claude Desktop. A ready copy is in [`mcp.json`](mcp.json).

### Codex

`~/.codex/config.toml`:

```toml
[mcp_servers.peopleperhour]
command = "/path/to/peopleperhour-api-mcp-server/.venv/bin/peopleperhour-mcp"
args = ["mcp"]
```

### Over HTTP

`peopleperhour-mcp serve` also serves MCP over streamable HTTP at `http://127.0.0.1:8787/mcp`, for clients that take a URL:

```bash
peopleperhour-mcp serve
claude mcp add --transport http peopleperhour http://127.0.0.1:8787/mcp
```

Then ask your agent things like:

> *Check PeoplePerHour for web design projects posted since yesterday, skip anything under £200 or with more than 15 proposals, read the briefs of the rest and give me a shortlist of five.*
>
> *Read the brief of project 4527712, open the files the buyer attached, list what I must deliver and the questions I have to answer, and draft a proposal I can paste.*
>
> *Is project 4527712 still open, and how many proposals does it have now?*
>
> *Find logo designers rated 80% or more at £10 to £30 an hour, read the profiles and recent reviews of the top five, and tell me which three to contact.*
>
> *Save a search for urgent fixed-price design projects called "Urgent design" with a daily email.*

## REST API

```bash
peopleperhour-mcp serve                    # http://127.0.0.1:8787, MCP at /mcp, docs at /docs
```

Each tool has its own route under `/api/v1/peopleperhour`, the same paths as the hosted API at cotlet.dev, so code written against one works with the other. Path parts and the query string are arguments.

```bash
curl 'http://127.0.0.1:8787/api/v1/peopleperhour/projects/search?query=web%20design&since=2026-10-21T07:00:00Z&limit=20'
curl 'http://127.0.0.1:8787/api/v1/peopleperhour/projects/4527712'
curl 'http://127.0.0.1:8787/api/v1/peopleperhour/freelancers/search?query=logo%20design&min_rating=80'
curl -X PUT 'http://127.0.0.1:8787/api/v1/peopleperhour/projects/4527712/watch'
```

Any tool by name, body as its arguments:

```bash
curl -X POST http://127.0.0.1:8787/api/v1/peopleperhour/tools/search_projects -d '{"category": "design", "limit": 10}'
```

- `GET /api/v1/peopleperhour/tools`: every tool with its route, input schema and an example answer.
- `GET /docs`: interactive OpenAPI docs, `GET /openapi.json` the schema, for n8n, Postman or a generated client.
- Answers are JSON. List tools return `next_cursor`; pass it back as `cursor` for the next page.

The server listens on `127.0.0.1` only. To reach it from another device of yours, set a token, and every request then needs `Authorization: Bearer <token>`:

```bash
PEOPLEPERHOUR_MCP_TOKEN=$(openssl rand -hex 24) peopleperhour-mcp serve --host 0.0.0.0
```

## Python and the example scripts

Straight from Python, no server needed:

```python
from peopleperhour_api_mcp import call
from peopleperhour_api_mcp.scripting import paginate, write_rows

new = list(paginate("search_projects", {"query": "logo", "since": "2026-10-21T00:00:00Z"}, "projects"))
write_rows(new, "projects.csv")
brief = call("get_project", project_id=new[0]["project_id"])["brief"]
```

Or one tool from the shell: `peopleperhour-mcp call get_project project_id=4527712`, or with a JSON object.

Ready scripts in [`examples/`](examples/), one per job on the [integration page](https://cotlet.dev/integrations/peopleperhour-api-mcp-server). Each takes `--help`, and the list scripts take `--out file.csv` or `--out file.json`:

| Script | What it does |
|---|---|
| [`find_new_projects.py`](examples/find_new_projects.py) | New projects for one or more keywords in the last N hours, merged, cut on `--min-budget` (or `--hourly-rate`) and `--max-proposals`, then the full brief, questions and files of each one left. |
| [`read_project_brief.py`](examples/read_project_brief.py) | One project before you write a proposal: brief, attached files, the buyer's questions, proposals, expiry and the 80% price floor. |
| [`watch_urgent_projects.py`](examples/watch_urgent_projects.py) | Urgent projects in a category with fewer than N proposals. `--state` remembers the last run, for an hourly cron job. |
| [`check_project_open.py`](examples/check_project_open.py) | Whether projects are still open and how many proposals each has now. |
| [`shortlist_freelancers.py`](examples/shortlist_freelancers.py) | Freelancers for a skill, cut on rate band and rating, with each profile's stats and the average of its latest reviews. |
| [`compare_offers.py`](examples/compare_offers.py) | The top Offers for a job side by side: price, delivery days, sales, add-ons and what the seller needs from you. |
| [`save_project_alert.py`](examples/save_project_alert.py) | Save a project search with filters and a daily or instant email alert, then list your saved searches. |
| [`buyer_daily_digest.py`](examples/buyer_daily_digest.py) | For a buyer: your open projects with proposal counts, unread notifications and WorkStreams with unread messages. |
| [`median_budgets.py`](examples/median_budgets.py) | Median fixed and hourly budgets per freelancer level for the categories you name, in GBP, USD or EUR. |

```bash
python examples/find_new_projects.py --query "web design" --query webflow --hours 24 --min-budget 200 --max-proposals 15
python examples/read_project_brief.py 4527712
python examples/shortlist_freelancers.py "logo design" --hourly-rate 10-30 --min-rating 80
python examples/median_budgets.py translation --currency USD
```

On a schedule, cron on your own computer works while it is on: `0 * * * * cd ~/peopleperhour-api-mcp-server && .venv/bin/python examples/watch_urgent_projects.py --category design --state urgent.json`.

Budgets are compared as PeoplePerHour gives them, in the buyer's currency (GBP, EUR or USD), so a floor of 200 means 200 of whatever the buyer picked.

## All 17 tools

`peopleperhour-mcp tools` prints this list, `peopleperhour-mcp tools --json` adds the input schemas. Times are UTC.

### Projects

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `search_projects` | read | `GET /projects/search` | Open projects buyers posted, newest first, with budget, category, proposals and the brief's start. |
| `get_project` | read | `GET /projects/{project_id}` | One project's full brief with budget, attachments, interview questions, buyer and proposal count. |
| `list_my_projects` | read | `GET /projects/mine` | Projects this account posted as a buyer, with status, budget and proposal count. |

### Watchlist

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `watch_project` | write | `PUT /projects/{project_id}/watch` | Add a project to this account's watchlist (Favourite Jobs) to come back to it later. |
| `unwatch_project` | write | `DELETE /projects/{project_id}/watch` | Take a project off this account's watchlist. |
| `list_watchlist` | read | `GET /projects/watched` | Open projects on this account's watchlist (Favourite Jobs), with budget and proposal count. |

### Saved searches

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_saved_searches` | read | `GET /saved-searches` | This account's saved project searches with their filters and email alert setting. |
| `save_search` | write | `POST /saved-searches` | Save a project search with an email alert, or rename one or change how often it emails. |
| `delete_saved_search` | write | `DELETE /saved-searches/{saved_search_id}` | Delete one of this account's saved project searches and its email alert. |

### Freelancers

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `search_freelancers` | read | `GET /freelancers/search` | Freelancers by skill or keyword, with rate, rating, reviews, completed projects and skills. |
| `get_freelancer` | read | `GET /freelancers/{freelancer_id}` | A freelancer's public profile: rate, stats, skills, portfolio and the latest reviews on the page. |

### Offers

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `search_offers` | read | `GET /offers/search` | Fixed-price Offers freelancers sell, by keyword or price, with sales, rating and seller. |
| `get_offer` | read | `GET /offers/{offer_id}` | One Offer with its full description, what the seller needs from you, prices, add-ons and images. |

### Account, notifications and WorkStreams

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `get_account` | read | `GET /account` | The signed-in PeoplePerHour account: name, type, buyer stats, unread messages and favourite counts. |
| `list_notifications` | read | `GET /notifications` | The latest notifications of this account (proposals, messages, project updates) and unread counts. |
| `list_workstreams` | read | `GET /workstreams` | This account's WorkStreams (conversations with hired freelancers) with the last message. |

### Categories

| Tool | Access | REST route | What it does |
|---|---|---|---|
| `list_categories` | read | `GET /categories` | The 10 project categories with their subcategories and typical budgets per freelancer level. |

`since` makes polling cheap: an agent passes the time of its last check and reads only what arrived after it. One call with `since` scans at most the 200 newest projects, so a page can hold fewer than `limit` and still have a `next_cursor`.

Budgets, rates and prices come as PeoplePerHour gives them: a project in the buyer's currency, freelancer rates, Offers and median budgets in your account currency or the one you pick.

Not in this version: the freelancer side (proposals, your seller profile, your own Offers), posting or editing projects, sending messages in WorkStreams, accepting proposals, and payments, invoices and Proposal credits.

Never built, on purpose: your PeoplePerHour sign-in, email, password and settings, and anything that moves money (Proposal credits, subscriptions, payments). Every request passes a guard that refuses any change to those PeoplePerHour paths.

## Configuration

| Variable | Default | What it does |
|---|---|---|
| `PEOPLEPERHOUR_MCP_HOME` | `~/.config/peopleperhour-api-mcp` | Folder of `session.json`. |
| `PEOPLEPERHOUR_AUTH_TOKEN` | | PeoplePerHour `api` cookie, instead of `peopleperhour-mcp connect`. |
| `PEOPLEPERHOUR_PROXY` | | Proxy for every request to PeoplePerHour, e.g. `http://user:pass@host:port`. |
| `PEOPLEPERHOUR_MCP_READ_ONLY` | | `1` hides and refuses the 4 tools that change PeoplePerHour: watchlist and saved searches (same as `--read-only`). |
| `PEOPLEPERHOUR_MCP_TOKEN` | | Bearer token required by `serve`; needed to listen beyond `127.0.0.1`. |
| `PEOPLEPERHOUR_MCP_HOST`, `PEOPLEPERHOUR_MCP_PORT` | `127.0.0.1`, `8787` | Address of `serve`. |

## Security and your PeoplePerHour account

- **Your password never reaches this code.** Only cookies are read, and only those of peopleperhour.com.
- **The session file is yours.** `session.json` is created with mode 0600. Anyone who has it can act as you on PeoplePerHour, so keep it out of git and shared folders.
- **Local by default.** `serve` binds to `127.0.0.1` and refuses another address without `PEOPLEPERHOUR_MCP_TOKEN`.
- **peopleperhour.com only.** Requests and redirects outside peopleperhour.com are refused. Attachment links point to PeoplePerHour's file host; the server returns them and does not download them.
- **Your own lists only.** 13 tools read. The 4 writes change your watchlist and saved searches and nothing else: no proposal, message or Offer purchase goes to anyone. A watched project lists you among its watchers, so unwatch what you no longer follow.
- **Keep the pace human.** A cron job every hour is fine. Hundreds of calls a minute is not how a person browses, and you are responsible for what runs in your account.

## Errors

The REST API answers `{"error": "<code>", "message": "..."}`. The MCP server returns the same code and message as a tool error.

| Status | Code | What to do |
|---|---|---|
| 401 | `auth_required`, `auth_expired` | No session, or PeoplePerHour signed you out. Sign in to PeoplePerHour in Chrome and run `peopleperhour-mcp connect`. |
| 403 | `target_blocked` | PeoplePerHour refused the request or showed a bot check. Open peopleperhour.com in Chrome once, then retry. |
| 409 | `captcha_required` | PeoplePerHour asks for a CAPTCHA. Solve it in Chrome. |
| 422 | `invalid_input` | An argument is missing or wrong; the message names it. |
| 429 | `rate_limited` | PeoplePerHour is limiting the account. Wait a few minutes. |
| 502 | `target_error` | No such project, freelancer, Offer or saved search, a private or removed one, a filter PeoplePerHour refused (the message gives its reason), or PeoplePerHour answered with an error or changed its site. `git pull` for the latest tools, or [open an issue](https://github.com/cotletdev/peopleperhour-api-mcp-server/issues). |

## Self-hosted or hosted

| | This repo | [Cotlet, hosted](https://cotlet.dev/integrations/peopleperhour-api-mcp-server) |
|---|---|---|
| Tools | the same 17 | the same 17 |
| Runs | on your computer, while it is on | in the cloud, 24/7 |
| PeoplePerHour session | your Chrome, cookies in a local file | your own Cloud Browser in the EU, profile encrypted with AES-256-GCM |
| When PeoplePerHour changes its site | `git pull` once we have fixed it | fixed for you, every tool tested daily |
| Works with | MCP clients on your machine, local scripts | Claude.ai and ChatGPT connectors, n8n, Make, Zapier, any HTTP client |
| Who may use it | you, for noncommercial use | teams, businesses, agencies |
| Price | free | free 7-day trial with 2,000 credits, no card; then one-time packs from $29 for 5,000 credits |

On the hosted version a successful call uses 20 to 30 credits (25 for most tools), failed calls are free, and the Cloud Browser uses 50 credits a day while it has an app enabled for agents. [Full pricing](https://cotlet.dev/pricing).

## FAQ

**Does PeoplePerHour have an official API?**
No. PeoplePerHour has no public API, no developer docs and no webhooks (checked 12 Oct 2026). The one built-in alert is Saved Searches: up to 10 searches on the Jobs page, each emailing new results instantly or once a day. PeoplePerHour gives you nothing to call them from code; here `save_search` and `list_saved_searches` manage them. Details: [cotlet.dev/integrations/peopleperhour-api-mcp-server](https://cotlet.dev/integrations/peopleperhour-api-mcp-server).

**Is there a PeoplePerHour MCP server for Claude, ChatGPT or Cursor?**
Yes, this one runs on your machine: `peopleperhour-mcp mcp` for Claude Code, Claude Desktop, Cursor and Codex. ChatGPT and Claude.ai connectors need a public HTTPS URL, which the [hosted PeoplePerHour MCP server](https://cotlet.dev/integrations/peopleperhour-api-mcp-server) gives you.

**Is this a PeoplePerHour scraper?**
It returns what people want a job scraper for (new projects with budget, proposals and brief, freelancers and Offers, as JSON or CSV) but runs no headless browser. It calls the same JSON endpoints the PeoplePerHour site calls, in your own account. The one HTML page it reads is a freelancer's profile, for the latest reviews.

**Can I get new PeoplePerHour projects as they are posted?**
Yes. Call `search_projects` with `since` set to your last check, from cron or an agent. [`watch_urgent_projects.py`](examples/watch_urgent_projects.py) keeps that time in a state file for you.

**Can it send proposals or answer buyers?**
No. Proposals, WorkStream messages, buying Offers, invoices and your Proposal credits are not in this version, and it spends no credits. It can read your WorkStreams and notifications. You write and send proposals and messages on PeoplePerHour yourself.

**Can I hire on PeoplePerHour with it?**
It helps you choose: `search_freelancers` and `get_freelancer` for profiles and recent reviews, `search_offers` and `get_offer` for fixed-price Offers, `list_categories` for what buyers usually pay. Posting the project, contacting a freelancer and paying stay on PeoplePerHour.

**Do I need a paid PeoplePerHour plan or a freelancer account?**
No. A free buyer account is enough for all 17 tools.

**Does get_project return the project's skills?**
No, because PeoplePerHour's project data has no list of skills. The skills are in the brief text, which an agent reads.

**Why does it need my Chrome?**
To read your PeoplePerHour session without your password. Chrome is used once per sign-in, not for each call.

**What happens when PeoplePerHour signs me out?**
Calls fail with `auth_expired`. With Chrome remote debugging on, the server reads the new cookies on the next call (click Allow when Chrome asks); otherwise run `peopleperhour-mcp connect` again.

**Can it run on a VPS or in Docker?**
Technically yes, with `PEOPLEPERHOUR_AUTH_TOKEN`. PeoplePerHour then sees your session from a datacenter IP, which looks less like you. For an always-on setup the hosted version keeps your session in your own Cloud Browser on a fixed IP.

**Will my PeoplePerHour account get banned?**
Requests carry Chrome's fingerprint and go out one at a time, and the tools read only what you could open yourself. Nobody can promise a platform never acts. Keep the polling to what a person would do.

**Can I use it at work or for my clients?**
No, the license allows noncommercial use only. For a team, a company or client work, use [Cotlet](https://cotlet.dev) or write to [contact@cotlet.dev](mailto:contact@cotlet.dev).

**Is it open source?**
The source is public, the license is not an open source license: noncommercial use only, no business use.

**A tool broke or I need another one.**
[Open an issue](https://github.com/cotletdev/peopleperhour-api-mcp-server/issues) with the tool name and the error message.

## License

[PolyForm Noncommercial License 1.0.0](LICENSE). In short:

- **Allowed:** noncommercial use: you, for your own personal purposes with your own PeoplePerHour account, or a charity, school, public research or government body. Changing the code, and sharing it under the same license.
- **Not allowed:** any commercial use, your own business included; client work; selling or offering it, or a service built on it.

---

<p>
  <a href="https://cotlet.dev">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="assets/logo-white.svg">
      <img src="assets/logo.svg" alt="Cotlet" width="120">
    </picture>
  </a>
</p>

Maintained by [Cotlet](https://cotlet.dev) ([@cotletdev](https://x.com/cotletdev)). PeoplePerHour is a trademark of its owner. This project is unofficial and not affiliated with, endorsed or sponsored by PeoplePerHour.
