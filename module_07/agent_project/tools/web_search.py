"""Web search tool: scrapes Bing results via primp + lxml (no API key)."""

import base64
from urllib.parse import parse_qs, urlparse

import primp
from lxml.html import document_fromstring

SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information. Use this for recent events, "
            "facts that may have changed since your training, or anything you're "
            "not confident about. Returns a list of results with title, url, and "
            "a short snippet."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Number of results to return (default 5, max 10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}

_MAX_SNIPPET_CHARS = 400


def _real_url(href):
    """Decode bing.com/ck/a tracking links to the actual destination URL."""
    if not href.startswith("https://www.bing.com/ck/a?"):
        return href
    encoded = parse_qs(urlparse(href).query).get("u", [""])[0]
    if len(encoded) <= 2:
        return href
    try:
        payload = encoded[2:] + "=" * (-(len(encoded) - 2) % 4)
        return base64.urlsafe_b64decode(payload).decode()
    except (ValueError, UnicodeDecodeError):
        return href


def execute(query: str, max_results: int = 5):
    max_results = max(1, min(max_results, 10))

    with primp.Client(impersonate="random", timeout=10) as client:
        resp = client.request("GET", "https://www.bing.com/search", params={"q": query})

    if resp.status_code != 200:
        raise ValueError(f"Search engine returned HTTP {resp.status_code}")

    results = []
    seen = set()
    for el in document_fromstring(resp.text).xpath("//li[contains(@class, 'b_algo')]"):
        hrefs = el.xpath("./h2/a/@href | ./div[contains(@class, 'header')]/a/@href")
        if not hrefs:
            continue
        url = _real_url(str(hrefs[0]))
        if url in seen:
            continue
        seen.add(url)

        title = "".join(el.xpath("./h2/a//text() | ./div[contains(@class, 'header')]/a/h2//text()")).strip()
        snippet = " ".join("".join(el.xpath(".//p//text()")).split())
        results.append({"title": title, "url": url, "snippet": snippet[:_MAX_SNIPPET_CHARS]})

        if len(results) >= max_results:
            break

    if not results:
        return {"query": query, "results": [], "note": "No results found"}
    return {"query": query, "results": results}
