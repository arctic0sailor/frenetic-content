"""Deterministic check that a question's anchorText appears verbatim in the
live article. Text fragments (#:~:text=) match rendered page text; the
MediaWiki plaintext extract is a close, cheap approximation — the Claude
verifier double-checks against the real page."""
import json
import re
import urllib.parse
import urllib.request

USER_AGENT = "frenetic-content/1.0 (https://waterfly.blue; harish@waterfly.blue)"


def _normalize(text):
    return re.sub(r"\s+", " ", text).strip()


def anchor_present(anchor, article_text):
    return _normalize(anchor) in _normalize(article_text)


def _http_get(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch_plaintext(title, fetch=None):
    """Full plaintext of an enwiki article ('' if missing)."""
    fetch = fetch or _http_get
    params = urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2",
        "prop": "extracts", "explaintext": "1", "redirects": "1",
        "titles": title,
    })
    data = json.loads(fetch(f"https://en.wikipedia.org/w/api.php?{params}"))
    pages = data.get("query", {}).get("pages", [])
    return pages[0].get("extract", "") if pages else ""
