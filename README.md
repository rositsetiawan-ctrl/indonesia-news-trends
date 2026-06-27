# 🤖 Tech & AI Indonesia News Trends → Nano Banana Social Posts

Automatically pull trending **Indonesian tech & AI news**, detect the hottest
stories, and turn each one into a ready-to-post social media package: a
**Nano Banana (Gemini) image prompt**, a **caption** (hype hook + explainer),
and **hashtags**.

Runs daily on **GitHub Actions** with no paid API keys.

```
Google News ID (tech) + tech portals  ──▶  fetch + niche filter  ──▶  cluster  ──▶  social posts
   (Detik Inet, Kompas Tekno, DailySocial,        keep only          trending      Nano Banana prompt
    Tech in Asia, CNBC Tech, Uzone…)              tech/AI stories    stories       + caption + hashtags
```

> **Niche:** technology, AI, startups, gadgets, and the digital economy in
> Indonesia. Want a different niche (finance, otomotif, esports)? Just edit the
> `search_queries`, `portals`, and `keyword_filter` in `config.yaml` — the
> engine stays the same.

---

## What you get each run

For the top trending stories (default 8), in `output/`:

| File | Description |
|------|-------------|
| `posts_<date>.md` | Human-readable, copy-paste ready posts |
| `posts_<date>.json` | Same posts as structured data |
| `trends_<date>.json` | Full analysis: keywords + story clusters |
| `latest.md` / `latest.json` | Convenience copy of the most recent run |

See **[docs/SAMPLE_OUTPUT.md](docs/SAMPLE_OUTPUT.md)** for an example.
> Note: the files currently in `output/` are a **sample generated from test
> data** (`tests/fixture_articles.json`). Delete them and run the pipeline to
> get real, live news.

Each post looks like:

> **🎨 Nano Banana image prompt** — paste into Nano Banana / Google AI Studio
> **✍️ Caption** — Indonesian (or English) caption with a hook + CTA
> **#️⃣ Hashtags** — topic-aware hashtags

---

## 1. Data sources

The **backbone is Google News Indonesia RSS** — free, no API key, very reliable.
It covers top stories plus topic sections (Nation, Business, Tech, Sports,
Entertainment, Science, Health).

Each major portal (Detik, Kompas, CNN Indonesia, Antara, Tempo, Tribun,
Liputan6) is pulled **through a Google News `site:` query**, so it keeps working
even when a portal's own RSS feed is down (Detik and Kompas have discontinued
theirs at times). Set `prefer_direct_rss: true` in `config.yaml` to use native
feeds first and fall back to Google News automatically.

Everything is configured in **`config.yaml`** — add/remove sources, change how
many stories, set caption language, etc.

## 2. Analysis

No heavy ML dependencies. The analyzer:

1. Scores keywords and bigrams across all headlines (Indonesian stopwords removed).
2. Clusters headlines that share top keywords → each cluster is one "story".
3. Ranks stories by article count + source diversity, so a topic covered by many
   outlets ranks highest.

## 3. Social post generation (Nano Banana)

Per request, **no image API is called** — the pipeline produces the **image
prompt** only. You paste it into Nano Banana (Gemini image generation in Google
AI Studio / Gemini app), generate the image, then post it with the provided
caption and hashtags.

**Image–news coherence.** The prompt builder doesn't use one generic visual for
everything. For each headline it:

1. detects **the event** — launch, funding, office opening, partnership,
   acquisition, cyberattack, regulation, data center, outage, update — and **the
   concrete subject** (smartphone, laptop, chip, robot, AI app, EV, crypto), then
   composes a scene that *depicts that specific event*;
2. **names the real-world brands/companies/places** in the headline (OpenAI,
   Samsung Galaxy, GoTo, Tokopedia, Jakarta, Indonesia…) and tells the model to
   show their real likeness — so the audience instantly recognizes the story;
3. **adds text on the image**: a bold UPPERCASE **hook headline** across the top
   plus a short **sub-headline** description, ready as a scroll-stopping cover.

Each post in the output therefore also lists the **on-image header**,
**sub-headline**, and **featured entities**. Tune any of this in
`EVENT_SCENES`, `SUBJECT_HINTS`, and `KNOWN_ENTITIES` in `src/generate_posts.py`.

> **Want even tighter coherence?** Rule-based detection covers the common event
> types and falls back to a neutral scene for unusual headlines. For
> best-in-class fidelity you can have an LLM (e.g. free-tier **Gemini Flash**)
> rewrite each headline into a bespoke image prompt. Ask and this can be wired
> into `generate_posts.py` behind your own API key.

---

## Quick start (local)

```bash
git clone <your-repo-url> indonesia-news-trends
cd indonesia-news-trends
pip install -r requirements.txt

# run the full pipeline against live news
python src/pipeline.py

# open the result
cat output/latest.md
```

Run against the offline test fixture (no network needed):

```bash
NEWS_FIXTURE=tests/fixture_articles.json python src/pipeline.py
```

---

## Automate with GitHub Actions

1. Create a new GitHub repository and push these files:

   ```bash
   git init
   git add .
   git commit -m "Initial commit: Indonesia news trends pipeline"
   git branch -M main
   git remote add origin https://github.com/<you>/indonesia-news-trends.git
   git push -u origin main
   ```

2. The workflow is already at `.github/workflows/daily-news.yml`. It:
   - runs every day at **00:30 UTC (~07:30 WIB)** and on manual trigger,
   - installs deps, runs the pipeline,
   - commits the new `output/` files back to the repo.

3. Enable write access for Actions:
   **Repo → Settings → Actions → General → Workflow permissions →
   "Read and write permissions"**. (The workflow also requests
   `contents: write`.)

4. Trigger it manually the first time:
   **Repo → Actions → "Daily Indonesia News Trends" → Run workflow.**

After it runs, your latest posts are always at `output/latest.md`.

---

## Configuration cheatsheet (`config.yaml`)

| Key | What it does |
|-----|--------------|
| `lookback_days` | How recent an article must be (Google News `when:Xd`) |
| `top_stories` | How many trending stories become posts |
| `min_cluster_size` | Min articles for a topic to count as trending |
| `caption_lang` | `id` (Indonesian) or `en` (English) captions |
| `caption_style` | `mix` (hook + explainer), `hype`, or `explainer` |
| `google_news.topics` | Which Google News ID sections to pull |
| `search_queries` | Niche search terms run against Google News (the heart of the niche) |
| `portals` | Niche sources + optional native RSS URLs |
| `keyword_filter` | Whole-word terms; an article is kept only if its title matches one |
| `prefer_direct_rss` | Use native RSS first, Google News as fallback |

### Switching niches later

To point this at a different niche, change three things in `config.yaml`:
`search_queries` (what to search), `portals` (which outlets), and
`keyword_filter.any_of` (what counts as on-topic). Optionally tweak the
`SCENE_HINTS` and `HASHTAG_BASE` in `src/generate_posts.py` for matching visuals.

---

## Project structure

```
indonesia-news-trends/
├── config.yaml                 # sources & options
├── requirements.txt
├── src/
│   ├── fetch_news.py           # Google News + portals
│   ├── analyze_trends.py       # keyword scoring + story clustering
│   ├── generate_posts.py       # Nano Banana prompt + caption + hashtags
│   ├── pipeline.py             # fetch → analyze → generate → write
│   └── utils.py                # config, tokenizing, stopwords
├── tests/fixture_articles.json # offline sample for testing
├── docs/SAMPLE_OUTPUT.md       # example output
├── output/                     # generated posts (committed by Actions)
└── .github/workflows/daily-news.yml
```

## Notes & tips

- **Faces & accuracy:** prompts deliberately exclude real, recognizable faces
  and any text. Always sanity-check generated images against the actual story
  before posting.
- **Tune the look:** edit `SCENE_HINTS` / the prompt template in
  `src/generate_posts.py` to match your brand style.
- **Want real images auto-generated?** Add a Gemini image API call in
  `generate_posts.py` using your own API key — the prompt is already built for you.
