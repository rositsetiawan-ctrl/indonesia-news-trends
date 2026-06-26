"""Rank trending topics and cluster headlines into trending stories.

Approach (no external ML deps):
  1. Score keywords/bigrams by frequency across all headlines.
  2. Cluster headlines that share top keywords -> each cluster = one "story".
  3. Rank stories by (article count + source diversity + keyword weight).
"""
from __future__ import annotations

from collections import Counter, defaultdict

from utils import bigrams, tokenize


def keyword_scores(articles: list[dict]) -> Counter:
    counter: Counter = Counter()
    for a in articles:
        toks = tokenize(a["title"])
        counter.update(toks)
        counter.update(bigrams(toks))  # bigrams capture names like "prabowo subianto"
    return counter


def _article_keywords(article: dict, top_terms: set[str]) -> set[str]:
    toks = tokenize(article["title"])
    terms = set(toks) | set(bigrams(toks))
    return terms & top_terms


def cluster_stories(articles: list[dict], min_cluster_size: int = 2,
                    top_keyword_n: int = 120) -> list[dict]:
    scores = keyword_scores(articles)
    # Prefer multi-word terms slightly (more specific) and drop singletons.
    ranked = [t for t, c in scores.most_common(top_keyword_n) if c >= 2]
    top_terms = set(ranked)

    # Greedy clustering: anchor on the most significant shared keyword.
    clusters: dict[str, list[dict]] = defaultdict(list)
    assigned: set[int] = set()
    for term in ranked:
        members = []
        for idx, art in enumerate(articles):
            if idx in assigned:
                continue
            if term in _article_keywords(art, top_terms):
                members.append((idx, art))
        if len(members) >= min_cluster_size:
            for idx, art in members:
                assigned.add(idx)
                clusters[term].append(art)

    stories = []
    for term, members in clusters.items():
        sources = sorted({m["source"] for m in members})
        # Headline = the shortest, most "headline-like" title in the cluster.
        rep = min(members, key=lambda m: len(m["title"]))
        kw = keyword_scores(members)
        keywords = [t for t, _ in kw.most_common(8) if " " not in t][:6]
        stories.append(
            {
                "topic": term,
                "headline": rep["title"],
                "link": rep["link"],
                "article_count": len(members),
                "source_count": len(sources),
                "sources": sources,
                "keywords": keywords,
                "score": len(members) * 2 + len(sources) * 3,
                "samples": [m["title"] for m in members[:5]],
            }
        )
    stories.sort(key=lambda s: s["score"], reverse=True)
    return stories


def top_keywords(articles: list[dict], n: int = 25) -> list[dict]:
    scores = keyword_scores(articles)
    out = []
    for term, count in scores.most_common(n * 3):
        if count < 2:
            continue
        out.append({"term": term, "count": count})
        if len(out) >= n:
            break
    return out


def analyze(articles: list[dict], cfg: dict) -> dict:
    min_size = cfg.get("min_cluster_size", 2)
    stories = cluster_stories(articles, min_cluster_size=min_size)
    return {
        "total_articles": len(articles),
        "trending_keywords": top_keywords(articles),
        "trending_stories": stories,
    }
