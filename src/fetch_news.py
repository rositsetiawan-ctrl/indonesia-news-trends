"""Fetch Indonesian news from Google News ID + major portals.

Everything can route through Google News RSS (no API key, very reliable),
with each portal pulled via a `site:` query so it keeps working even when the
portal's own RSS feed is down. Native RSS feeds are used when configured and
`prefer_direct_rss` is true.
"""
from __future__ import annotations

import time
from urllib.parse import quote_plus

from utils import load_config, normalize

UA = "Mozilla/5.0 (compatible; IndonesiaNewsTrends/1.0; +https://github.com/)"
GN_BASE = "https://news.google.com/rss"


def _gn_params(cfg: dict) -> str:
    g = cfg["google_news"]
    return f"hl={g['hl']}&gl={g['gl']}&ceid={quote_plus(g['ceid'])}"


def _fetch(url: str, timeout: int = 25):
    """Fetch a URL and hand bytes to feedparser (more reliable than passing URL)."""
    import feedparser  # lazy import: not needed for offline/fixture runs
    import requests
    try:
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=timeout)
        resp.raise_for_status()
        return feedparser.parse(resp.content)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! fetch failed: {url[:80]} -> {exc}")
        return None


def _entries(parsed, source: str, limit: int = 60) -> list[dict]:
    if not parsed or not getattr(parsed, "entries", None):
        return []
    items = []
    for e in parsed.entries[:limit]:
        title = normalize(getattr(e, "title", ""))
        if not title:
            continue
        items.append(
            {
                "title": title,
                "link": getattr(e, "link", ""),
                "published": getattr(e, "published", "") or getattr(e, "updated", ""),
                "source": source,
                "summary": normalize(getattr(e, "summary", ""))[:400],
            }
        )
    return items


def fetch_google_topics(cfg: dict) -> list[dict]:
    out: list[dict] = []
    params = _gn_params(cfg)
    # Top stories
    print("Google News ID: top stories")
    out += _entries(_fetch(f"{GN_BASE}?{params}"), "Google News (Top)")
    # Topic sections
    for topic in cfg["google_news"].get("topics", []):
        print(f"Google News ID: topic {topic}")
        url = f"{GN_BASE}/headlines/section/topic/{topic}?{params}"
        out += _entries(_fetch(url), f"Google News ({topic.title()})")
        time.sleep(0.5)
    return out


def fetch_portals(cfg: dict) -> list[dict]:
    out: list[dict] = []
    params = _gn_params(cfg)
    lookback = cfg.get("lookback_days", 1)
    prefer_direct = cfg.get("prefer_direct_rss", False)
    for p in cfg.get("portals", []):
        name = p["name"]
        direct = p.get("direct_rss", "")
        if prefer_direct and direct:
            print(f"{name}: direct RSS")
            got = _entries(_fetch(direct), name)
            if got:
                out += got
                continue  # success; skip Google News fallback
            print(f"  {name}: direct RSS empty, falling back to Google News")
        # Route through Google News site: search (robust)
        print(f"{name}: via Google News site:{p['site']}")
        q = quote_plus(f"when:{lookback}d site:{p['site']}")
        url = f"{GN_BASE}/search?q={q}&{params}"
        out += _entries(_fetch(url), name)
        time.sleep(0.5)
    return out


def dedupe(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out = []
    for it in items:
        key = it["title"].lower().strip()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out


def fetch_all(cfg: dict) -> list[dict]:
    items: list[dict] = []
    if cfg.get("google_news", {}).get("enabled", True):
        items += fetch_google_topics(cfg)
    items += fetch_portals(cfg)
    items = dedupe(items)
    print(f"\nFetched {len(items)} unique articles.")
    return items


if __name__ == "__main__":
    conf = load_config()
    arts = fetch_all(conf)
    for a in arts[:15]:
        print(f"- [{a['source']}] {a['title']}")
