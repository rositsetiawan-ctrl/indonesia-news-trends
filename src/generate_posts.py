"""Turn trending stories into ready-to-use social posts:
   - a Nano Banana (Gemini image) prompt
   - a caption (Indonesian or English)
   - hashtags

No image API is called here (per request: prompts only). You paste the prompt
into Nano Banana / Google AI Studio yourself, then post with the caption.
"""
from __future__ import annotations

import re

from utils import slugify, tokenize

# Map source/topic hints -> a visual scene direction for the image model.
SCENE_HINTS = {
    "politik": "Indonesian government building, formal press-conference atmosphere",
    "ekonomi": "Jakarta financial district skyline, stock ticker and rupiah motifs",
    "rupiah": "Indonesian rupiah banknotes and a rising/falling market chart",
    "bola": "dynamic football stadium under floodlights, Indonesian supporters",
    "sepak": "dynamic football stadium under floodlights, Indonesian supporters",
    "timnas": "Garuda red-and-white football kit, packed national stadium",
    "gempa": "seismograph waves over an Indonesian map, emergency-response mood",
    "banjir": "flooded Indonesian street, dramatic overcast sky, rescue boats",
    "cuaca": "Indonesian sky and weather map, atmospheric clouds",
    "teknologi": "futuristic tech interface, circuit motifs, modern Indonesian city",
    "ai": "glowing neural-network motifs over a modern Indonesian skyline",
    "film": "cinematic spotlight, red-carpet premiere, film-reel motifs",
    "konser": "concert stage with vivid lighting and a large crowd",
    "harga": "marketplace and price-tag motifs, Indonesian context",
    "bbm": "fuel pump and rupiah motifs, Indonesian gas station",
    "pemilu": "ballot box and Indonesian flag motifs, civic atmosphere",
    "presiden": "Indonesian presidential palace, formal state setting",
}

DEFAULT_SCENE = "modern Indonesian newsroom backdrop, Garuda red-and-white accent"

HASHTAG_BASE = ["#BeritaIndonesia", "#TrendingIndonesia", "#NewsUpdate", "#Indonesia"]


def _scene_for(story: dict) -> str:
    haystack = (story["headline"] + " " + " ".join(story["keywords"])).lower()
    for key, scene in SCENE_HINTS.items():
        if key in haystack:
            return scene
    return DEFAULT_SCENE


def build_image_prompt(story: dict) -> str:
    scene = _scene_for(story)
    headline = story["headline"]
    return (
        "Editorial news illustration, 1:1 square, social-media ready. "
        f"Subject: {headline}. "
        f"Scene: {scene}. "
        "Style: clean modern infographic-poster, bold focal subject, soft depth of field, "
        "professional photojournalism lighting, high contrast, vibrant but credible colors. "
        "Composition: leave clear negative space at the top for a headline overlay. "
        "Add a subtle Indonesian red-and-white color accent. "
        "No real recognizable faces, no text in the image, no watermarks, no logos. "
        "Photorealistic with a touch of editorial graphic design. --ar 1:1"
    )


def _title_case_id(text: str) -> str:
    return text.strip().rstrip(".")


def build_caption(story: dict, lang: str = "id") -> str:
    headline = _title_case_id(story["headline"])
    n = story["article_count"]
    srcs = ", ".join(story["sources"][:3])
    if lang == "en":
        body = (
            f"🔥 TRENDING IN INDONESIA\n\n"
            f"{headline}\n\n"
            f"This story is making waves — covered across {n} reports "
            f"({srcs}). What's your take? 👇\n\n"
            f"Save & share to keep up with Indonesia's top news."
        )
    else:
        body = (
            f"🔥 LAGI RAME DI INDONESIA\n\n"
            f"{headline}\n\n"
            f"Topik ini lagi jadi sorotan — dibahas di {n} pemberitaan "
            f"({srcs}). Menurut kamu gimana? 👇\n\n"
            f"Simpan & bagikan biar nggak ketinggalan berita terbaru."
        )
    return body


def build_hashtags(story: dict, limit: int = 12) -> list[str]:
    tags = list(HASHTAG_BASE)
    for kw in story["keywords"]:
        parts = [p for p in re.split(r"\s+", kw) if p]
        tag = "#" + "".join(w.capitalize() for w in parts)
        if len(tag) > 2 and tag not in tags:
            tags.append(tag)
    return tags[:limit]


def make_posts(analysis: dict, cfg: dict) -> list[dict]:
    lang = cfg.get("caption_lang", "id")
    top_n = cfg.get("top_stories", 8)
    posts = []
    for rank, story in enumerate(analysis["trending_stories"][:top_n], start=1):
        posts.append(
            {
                "rank": rank,
                "slug": slugify(story["headline"]),
                "topic": story["topic"],
                "headline": story["headline"],
                "link": story["link"],
                "article_count": story["article_count"],
                "sources": story["sources"],
                "keywords": story["keywords"],
                "image_prompt": build_image_prompt(story),
                "caption": build_caption(story, lang),
                "hashtags": build_hashtags(story),
            }
        )
    return posts
