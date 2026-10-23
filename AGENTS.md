# AGENTS.md

You are an AI agent in a clone of this repo. It is a self-hosted PeoplePerHour API and MCP server: 17 tools that search projects, freelancers and Offers, read briefs, profiles and Offers, keep a watchlist and saved searches, and read the account's own projects, notifications and WorkStreams in the user's own PeoplePerHour account, through the session of their own Google Chrome. Your usual job is one of three: set it up for the user, use its tools for them, or change its code. Human docs: `README.md`.

## Before you start

- The license allows noncommercial use only (PolyForm Noncommercial 1.0.0, `LICENSE`). If the user is setting this up for a company, a team or clients, say so and point to the hosted version at https://cotlet.dev/integrations/peopleperhour-api-mcp-server. Do not continue the setup for that use.
- 13 tools read. The other 4 (`watch_project`, `unwatch_project`, `save_search`, `delete_saved_search`) change only the user's own watchlist and saved searches. No tool sends proposals or messages, posts projects, buys Offers or spends Proposal credits. If the user asks you to send a proposal or a message, draft it and tell them to paste it into PeoplePerHour themselves.
- A watched project lists the user among its watchers. Unwatch what they no longer follow.

## Set it up for the user

Do the steps yourself. Ask the user only for what needs their hands in Chrome.

1. Check Python: `python3 --version` must be 3.11 or newer.
2. Install in the repo root:

   ```bash
   python3 -m venv .venv && .venv/bin/pip install -e .
   .venv/bin/peopleperhour-mcp --version
   ```

   On Windows the path is `.venv\Scripts\peopleperhour-mcp`. With uv: `uv venv && uv pip install -e .`.
3. Ask the user to do two things in Chrome. You cannot open `chrome://` pages for them.
   - Open `chrome://inspect/#remote-debugging` and switch remote debugging on.
   - Be signed in at https://www.peopleperhour.com/site/login, with **Remember me** ticked.
4. Run `.venv/bin/peopleperhour-mcp connect`. Tell the user to click **Allow** when Chrome asks about the connection. Success prints `Signed in to PeoplePerHour as <name> (<email>)`.
5. Check: `.venv/bin/peopleperhour-mcp status`, then `.venv/bin/peopleperhour-mcp call search_projects limit=3`.
6. Add the MCP server to the user's client. Use the absolute path of `.venv/bin/peopleperhour-mcp`:
   - Claude Code: `claude mcp add peopleperhour -- <abs path>/.venv/bin/peopleperhour-mcp mcp`
   - Claude Desktop, Cursor, Codex: the config blocks in `README.md`, section "MCP server".
   The client loads new MCP servers on its next start. Tell the user.

If step 4 fails:

| Message | What to do |
|---|---|
| `Chrome remote debugging is off` | Step 3 is not done, or Chrome is Beta, Canary or a custom profile: pass `--profile-dir "<profile folder>"`. |
| `Could not connect to Chrome` | The user did not click Allow, or Chrome is closed. Run `connect` again. |
| `This Chrome is not signed in to PeoplePerHour` | The user signs in at peopleperhour.com in that Chrome, then run `connect` again. |
| No Chrome on this machine (a server) | The user copies the `api` cookie from Chrome DevTools (Application, Cookies, https://www.peopleperhour.com) and runs `peopleperhour-mcp connect --token` themselves. Never ask them to paste the token into the chat. |

## Use the tools

- With the MCP server added, call its tools. Without it: `.venv/bin/peopleperhour-mcp call <tool> key=value ...`, or one JSON object as the argument.
- `.venv/bin/peopleperhour-mcp tools` lists all 17 tools with access and route. `tools --json` adds the input schemas.
- Start with `search_projects`. Its `project_id` values are what `get_project` and `watch_project` take; a project's page URL works too. In the same way `search_freelancers` gives `freelancer_id` for `get_freelancer`, and `search_offers` gives `offer_id` for `get_offer`.
- To find new work, pass `since` with the time of the last check. Times are UTC.
- List tools return `next_cursor`. Pass it back as `cursor` for the next page.
- PeoplePerHour allows 10 saved searches per account. Run `list_saved_searches` before `save_search`, and ask the user before `delete_saved_search`.
- Project budgets are in the buyer's currency. With `budget.type` `hourly` the amount is per hour. Freelancer rates and Offer prices are in the account currency.
- For a script or a cron job, use `peopleperhour_api_mcp.scripting` (`call`, `paginate`, `write_rows`) and the scripts in `examples/` as models. Poll at most a few times an hour.
- For a REST API (n8n, other languages): `.venv/bin/peopleperhour-mcp serve`, routes under `http://127.0.0.1:8787/api/v1/peopleperhour`, docs at `/docs`.

Errors come as `<code>: <message>`. `auth_expired` means PeoplePerHour signed the session out: the user signs in again in Chrome and you run `connect`. `target_error` from a `get_` tool also covers a private, removed or unknown item. More codes: `README.md`, section "Errors".

## Keep secrets out

- `~/.config/peopleperhour-api-mcp/session.json` and `PEOPLEPERHOUR_AUTH_TOKEN` give full access to the user's PeoplePerHour account. Never print, log, commit or copy their content.
- `serve` listens on 127.0.0.1. Never start it on another address without `PEOPLEPERHOUR_MCP_TOKEN`.

## Change the code

| Path | What | Edit? |
|---|---|---|
| `peopleperhour_api_mcp/peopleperhour/` | the PeoplePerHour tools, one file per tool in `tools/`, shared request code in `client.py` | Yes for a local fix, but the next `git pull` brings our version of these files. Report the bug at https://github.com/cotletdev/peopleperhour-api-mcp-server/issues |
| `peopleperhour_api_mcp/app.py` | app name, domains, session cookie, account paths, REST prefix | Rarely |
| `peopleperhour_api_mcp/core/` | `@tool` declaration, errors, the HTTP client with the session (`context.py`), the guard against account changes (`account_guard.py`) | Yes |
| `peopleperhour_api_mcp/session.py` | reading cookies from Chrome over CDP, the session file | Yes |
| `peopleperhour_api_mcp/runner.py`, `api.py`, `mcp_server.py`, `cli.py` | tool registry, REST API, MCP server, command line | Yes |
| `examples/` | scripts for common jobs | Yes |

A new tool is a new file in `peopleperhour_api_mcp/peopleperhour/tools/` with a `@tool(...)` declaration (name, access, input schema, `route`). The registry finds it, and the REST API, the MCP server and the CLI show it without other changes. Every `/v2` call goes through `client.v2`, which adds the fixed `app_id`/`app_key` pair the site's own code sends.

There is no test suite. After a change, run `.venv/bin/peopleperhour-mcp tools` and one read tool against the user's account.
