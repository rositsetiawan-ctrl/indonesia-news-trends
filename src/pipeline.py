"""End-to-end pipeline: fetch -> analyze -> generate posts -> write outputs.

Outputs (dated, in the configured output_dir):
  - trends_<date>.json     full structured data (articles summary, keywords, stories)
  - posts_<date>.json      social posts (image prompt + caption + hashtags)
  - posts_<date>.md        human-readable, copy-paste ready
  - latest.md / latest.json  convenience copies of the newest run
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from analyze_trends import analyze
from fetch_news import fetch_all
from generate_posts import make_posts
from utils import load_config, repo_path

# Allow running from anywhere (e.g. GitHub Actions) by injecting the offline
# fixture used in tests when NEWS_FIXTURE is set.
def _load_articles(cfg):
    fixture = os.environ.get("NEWS_FIXTURE")
    if fixture:
        with open(fixture, "r", encoding="utf-8") as fh:
            print(f"Using fixture: {fixture}")
            return json.load(fh)
    return fetch_all(cfg)


def _render_markdown(posts, analysis, date_str) -> str:
    lines = [
        f"# 🇮🇩 Trending News Indonesia — {date_str}",
        "",
        f"_Analyzed **{analysis['total_articles']}** articles · "
        f"**{len(analysis['trending_stories'])}** trending stories detected._",
        "",
        "## 🔝 Top trending keywords",
        "",
        ", ".join(
            f"`{k['term']}` ({k['count']})" for k in analysis["trending_keywords"][:20]
        ),
        "",
        "---",
        "",
        "## 📲 Social posts (Nano Banana prompt + caption + hashtags)",
        "",
    ]
    for p in posts:
        lines += [
            f"### {p['rank']}. {p['headline']}",
            "",
            f"- **Topic anchor:** `{p['topic']}`  ·  "
            f"**Coverage:** {p['article_count']} articles  ·  "
            f"**Sources:** {', '.join(p['sources'])}",
            f"- **Source link:** {p['link']}",
            "",
            "**🎨 Nano Banana image prompt**",
            "",
            "```text",
            p["image_prompt"],
            "```",
            "",
            "**✍️ Caption**",
            "",
            "```text",
            p["caption"],
            "```",
            "",
            "**#️⃣ Hashtags**",
            "",
            " ".join(p["hashtags"]),
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


def run():
    cfg = load_config()
    out_dir = repo_path(cfg.get("output_dir", "output"))
    os.makedirs(out_dir, exist_ok=True)

    articles = _load_articles(cfg)
    analysis = analyze(articles, cfg)
    posts = make_posts(analysis, cfg)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    stamp = now.strftime("%Y-%m-%d_%H%M")

    trends_payload = {
        "generated_at": now.isoformat(),
        "total_articles": analysis["total_articles"],
        "trending_keywords": analysis["trending_keywords"],
        "trending_stories": analysis["trending_stories"],
    }
    posts_payload = {"generated_at": now.isoformat(), "date": date_str, "posts": posts}
    md = _render_markdown(posts, analysis, date_str)

    def _write(name, content, is_json=False):
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            if is_json:
                json.dump(content, fh, ensure_ascii=False, indent=2)
            else:
                fh.write(content)
        print(f"  wrote {path}")

    _write(f"trends_{stamp}.json", trends_payload, is_json=True)
    _write(f"posts_{stamp}.json", posts_payload, is_json=True)
    _write(f"posts_{stamp}.md", md)
    _write("latest.json", posts_payload, is_json=True)
    _write("latest.md", md)

    print(f"\nDone. {len(posts)} social posts generated for {date_str}.")
    return posts_payload


if __name__ == "__main__":
    run()
