"""Everything the server knows about PeoplePerHour outside `peopleperhour/`: names, domains and the session cookie.

The rest of the package reads these values and never names the app itself.
"""

from __future__ import annotations

NAME = "PeoplePerHour"
SLUG = "peopleperhour"
# The command and the prefix of every environment variable (PEOPLEPERHOUR_AUTH_TOKEN, PEOPLEPERHOUR_MCP_TOKEN ...).
CLI = "peopleperhour-mcp"
ENV = "PEOPLEPERHOUR"
# Requests may reach only these hosts and their subdomains. Their cookies are read from Chrome.
# The site and its JSON API are both on www.peopleperhour.com; some cookies sit on .peopleperhour.com.
DOMAINS = ("peopleperhour.com",)
# Present only while signed in. The first is the cookie a pasted token sets.
SESSION_COOKIES = ("api",)
COOKIE_DOMAIN = "www.peopleperhour.com"
LOGIN_URL = "https://www.peopleperhour.com/site/login"
# A final URL with one of these means the app signed the session out.
LOGGED_OUT_MARKERS = ("/site/login",)
# Paths a tool may only read: sign-in, sign-up, the member's own record and the settings pages.
# Any method but GET, HEAD or OPTIONS to one of them is refused before it leaves (core/account_guard.py).
ACCOUNT_PATHS = (
    r"^/v1/user/",
    r"^/settings/",
    r"^/site/(login|register|verifyEmail)",
    r"^/v2/members/",
)
# A 401 or 403 whose body has one of these asks for a fresh sign-in, not a missing role. PeoplePerHour has none.
RELOGIN_MARKERS: tuple[str, ...] = ()
# REST routes live under this path, the same as on cotlet.dev.
API_PREFIX = "/api/v1/peopleperhour"
# Prepended to the MCP server's instructions: where an agent starts.
AGENT_START = (
    "Start with search_projects: its project_id values are what get_project takes. Both tools only read projects."
)
