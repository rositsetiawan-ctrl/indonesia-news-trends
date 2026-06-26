# 🇮🇩 Indonesia News Trends → Nano Banana Social Posts

Automatically pull trending Indonesian news, detect the hottest stories, and
turn each one into a ready-to-post social media package: a **Nano Banana
(Gemini) image prompt**, a **caption**, and **hashtags**.

Runs daily on **GitHub Actions** with no paid API keys.

```
Google News ID + major portals  ──▶  fetch  ──▶  analyze/cluster  ──▶  social posts
   (Detik, Kompas, CNN ID,                trending          Nano Banana prompt
    Antara, Tempo, Tribun…)               stories           + caption + hashtags
```

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
caption and hashtags. Prompts are tuned for a 1:1 editorial news look with space
for a headline overlay, and avoid real faces/text/logos.

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
| `google_news.topics` | Which Google News ID sections to pull |
| `portals` | Sources + optional native RSS URLs |
| `prefer_direct_rss` | Use native RSS first, Google News as fallback |

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
