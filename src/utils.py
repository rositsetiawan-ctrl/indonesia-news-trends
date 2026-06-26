"""Shared helpers: config loading, Indonesian text tokenizing, stopwords."""
from __future__ import annotations

import os
import re
import unicodedata

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config(path: str | None = None) -> dict:
    path = path or os.path.join(ROOT, "config.yaml")
    if yaml is None:
        raise RuntimeError("PyYAML is required. Run: pip install -r requirements.txt")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def repo_path(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


# Common Indonesian + English stopwords so trending keywords are meaningful.
STOPWORDS = set("""
yang di ke dari dan untuk pada dengan ini itu atau juga akan sudah belum tidak
ada karena saat saja oleh para adalah dalam sebagai agar bisa dapat lebih
hingga sampai antara setelah sebelum lalu kini telah masih hanya bagi tentang
tentang menjadi sebuah suatu kami kita kamu mereka dia ia nya pun kah lah
se ya tak nggak gak banyak semua setiap soal jadi buat punya per terkait
news indonesia berita video foto live update terbaru hari ini kabar info
the a an of to in on for and or is are was were be by with at from as it this
that he she they we you i his her its their our your not no yes new latest
breaking says said amid over after before vs viral simak begini ini soal
""".split())

# Lightweight English suffixes are ignored; we just lowercase + split.
WORD_RE = re.compile(r"[A-Za-zÀ-ÿ0-9']+")


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return text.strip()


def tokenize(text: str) -> list[str]:
    text = normalize(text).lower()
    tokens = WORD_RE.findall(text)
    out = []
    for t in tokens:
        if len(t) < 3:
            continue
        if t in STOPWORDS:
            continue
        if t.isdigit():
            continue
        out.append(t)
    return out


def bigrams(tokens: list[str]) -> list[str]:
    return [f"{tokens[i]} {tokens[i + 1]}" for i in range(len(tokens) - 1)]


def slugify(text: str, maxlen: int = 60) -> str:
    text = normalize(text).lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:maxlen] or "post"
