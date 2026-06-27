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

# ---------------------------------------------------------------------------
# Image coherence: depict what ACTUALLY happened in the headline.
#
# We detect (1) the EVENT (what happened) and (2) the SUBJECT (the concrete
# object/company involved), then compose a scene that shows that specific
# event. This is what makes the generated image match the news instead of a
# generic "AI brain over a skyline" for every story.
# ---------------------------------------------------------------------------

# Each event: (key, trigger words in the Indonesian headline, scene template).
# {subject} is filled with the detected concrete subject when present.
EVENT_SCENES = [
    ("funding",
     ["pendanaan", "danai", "didanai", "investasi", "investor", "suntikan dana",
      "raih dana", "seri a", "seri b", "seri c", "funding", "valuasi"],
     "a startup-funding moment: confident founders in a bright modern Jakarta "
     "office celebrating, a large screen showing a steep upward investment "
     "growth chart, stacks of Indonesian rupiah and venture-capital motifs"),

    ("acquisition",
     ["akuisisi", "caplok", "ambil alih", "merger", "akuisi"],
     "a corporate acquisition concept: two glowing company emblems merging into "
     "one, a handshake silhouette, a high-stakes financial deal atmosphere"),

    ("partnership",
     ["kerja sama", "kerjasama", "gandeng", "kolaborasi", "mitra", "kemitraan",
      "integrasi", "integrasikan", "partnership", "teken"],
     "a tech partnership concept: two business figures shaking hands, glowing "
     "network lines connecting two platforms, collaborative optimistic mood"),

    ("cyber",
     ["serangan siber", "diretas", "peretas", "hacker", "bocor", "kebocoran",
      "ransomware", "phishing", "malware", "dibobol", "keamanan siber", "cyber"],
     "a dramatic cybersecurity breach scene: a hooded hacker silhouette facing "
     "glowing screens of code, red alert warnings, a cracked digital padlock, "
     "dark high-tension control-room lighting"),

    ("regulation",
     ["aturan", "regulasi", "kominfo", "komdigi", "kebijakan", "perketat",
      "larang", "blokir", "denda", "diatur", "undang-undang", "ruu", "izin"],
     "an Indonesian digital-policy scene: an official government podium with "
     "the red-and-white Indonesian flag, holographic regulation and data-shield "
     "motifs, formal press-conference atmosphere"),

    ("expansion",
     ["buka kantor", "kantor baru", "ekspansi", "masuk pasar", "hadir di indonesia",
      "ekspansi ke", "dirikan", "bangun pusat", "investasi di indonesia"],
     "a grand-opening / expansion scene: a sleek modern corporate tech "
     "headquarters in Jakarta's business district at golden hour, ribbon-cutting "
     "atmosphere, optimistic and premium"),

    ("datacenter",
     ["data center", "pusat data", "server", "hyperscale", "infrastruktur digital"],
     "a vast futuristic data center in Indonesia: endless rows of server racks "
     "glowing blue, cinematic depth of field, cool high-tech atmosphere"),

    ("launch",
     ["rilis", "meluncur", "luncurkan", "diluncurkan", "hadirkan", "umumkan",
      "peluncuran", "unveil", "perkenalkan", "resmi hadir", "meluncurkan"],
     "a product-launch scene: {subject} revealed on a glowing launch-event "
     "stage under a dramatic spotlight, sleek hero product shot, audience "
     "silhouettes and a big screen"),

    ("outage",
     ["down", "gangguan", "tumbang", "lumpuh", "error", "trouble", "tidak bisa diakses"],
     "a service-outage concept: a giant glowing red error symbol hovering over "
     "a city, frustrated people looking at their phones, warning-toned lighting"),

    ("update",
     ["update", "fitur baru", "pembaruan", "versi baru", "upgrade"],
     "a software-update concept: {subject} with a glowing 'new feature' "
     "interface, sparkles and UI elements floating around a device"),
]

# Short Indonesian sub-headline per event (used when the headline has no clause
# after a comma to reuse).
EVENT_SUBTITLE_ID = {
    "funding": "Pendanaan baru guncang ekosistem startup",
    "acquisition": "Aksi akuisisi besar di dunia tech",
    "partnership": "Kolaborasi strategis dimulai",
    "cyber": "Ancaman keamanan digital meningkat",
    "regulation": "Aturan baru pemerintah Indonesia",
    "expansion": "Ekspansi besar ke pasar Indonesia",
    "datacenter": "Infrastruktur digital raksasa dibangun",
    "launch": "Produk teknologi terbaru resmi hadir",
    "outage": "Layanan tumbang, pengguna terdampak",
    "update": "Fitur baru menghadirkan perubahan",
}

# Real-world names to surface in the prompt so the image is recognizable.
# (Ambiguous Indonesian words like "dana", "mandiri", "ovo" are deliberately
# excluded to avoid false positives.)
KNOWN_ENTITIES = {
    "openai": "OpenAI", "chatgpt": "ChatGPT", "google": "Google",
    "gemini": "Google Gemini", "android": "Android", "deepseek": "DeepSeek",
    "anthropic": "Anthropic", "claude": "Claude AI",
    "apple": "Apple", "iphone": "iPhone", "ipad": "iPad", "macbook": "MacBook",
    "samsung": "Samsung", "galaxy": "Samsung Galaxy",
    "xiaomi": "Xiaomi", "redmi": "Redmi", "poco": "POCO", "oppo": "OPPO",
    "vivo": "vivo", "realme": "realme", "infinix": "Infinix", "tecno": "Tecno",
    "huawei": "Huawei", "asus": "ASUS", "lenovo": "Lenovo", "acer": "Acer",
    "microsoft": "Microsoft", "windows": "Windows", "copilot": "Microsoft Copilot",
    "meta": "Meta", "facebook": "Facebook", "instagram": "Instagram",
    "whatsapp": "WhatsApp", "tiktok": "TikTok", "bytedance": "ByteDance",
    "youtube": "YouTube", "nvidia": "NVIDIA", "intel": "Intel",
    "qualcomm": "Qualcomm", "snapdragon": "Snapdragon", "amd": "AMD",
    "tesla": "Tesla", "spacex": "SpaceX", "starlink": "Starlink",
    "goto": "GoTo", "gojek": "Gojek", "tokopedia": "Tokopedia", "grab": "Grab",
    "shopee": "Shopee", "bukalapak": "Bukalapak", "traveloka": "Traveloka",
    "blibli": "Blibli", "telkom": "Telkom", "telkomsel": "Telkomsel",
    "indosat": "Indosat", "gopay": "GoPay", "bca": "BCA",
    "amazon": "Amazon", "aws": "AWS", "netflix": "Netflix",
    "bitcoin": "Bitcoin", "ethereum": "Ethereum",
    "indonesia": "Indonesia", "jakarta": "Jakarta",
    "kominfo": "Kominfo", "komdigi": "Komdigi",
}

# Concrete subjects to feature in the scene (checked as whole-ish tokens).
SUBJECT_HINTS = [
    (["galaxy", "samsung", "iphone", "apple", "xiaomi", "redmi", "oppo", "vivo",
      "realme", "infinix", "tecno", "smartphone", "ponsel", "hp"],
     "a premium flagship smartphone"),
    (["laptop", "macbook", "notebook", "ultrabook"], "a sleek modern laptop"),
    (["chip", "prosesor", "semikonduktor", "gpu", "nvidia", "snapdragon"],
     "a glowing advanced semiconductor chip on a circuit board"),
    (["robot", "humanoid"], "an advanced humanoid robot"),
    (["mobil listrik", "kendaraan listrik", "ev ", "motor listrik"],
     "a futuristic electric vehicle"),
    (["aplikasi", "app", "platform", "fitur", "asisten", "chatbot", "model ai",
      "ai", "kecerdasan buatan", "generative", "chatgpt", "gemini"],
     "a glowing AI app interface on a smartphone, friendly digital-assistant motifs"),
    (["drone"], "a high-tech drone in flight"),
    (["kripto", "crypto", "bitcoin", "blockchain", "token"],
     "glowing crypto-coin and blockchain motifs"),
]

# Generic fallback (only used when nothing is detected).
DEFAULT_SCENE = (
    "a clean conceptual Indonesian tech-news scene relevant to the topic, "
    "modern devices and subtle data motifs on a studio backdrop"
)

HASHTAG_BASE = ["#TeknologiIndonesia", "#TechIndonesia", "#AIIndonesia",
                "#StartupIndonesia", "#BeritaTeknologi"]

# Words too generic to make good hashtags.
_HASHTAG_SKIP = {"resmi", "buka", "ini", "baru", "jadi", "akan", "usai", "raih",
                 "soal", "lagi", "hari", "kini", "dampaknya", "lengkapnya",
                 "terbaru", "begini", "simak", "viral", "bakal", "mulai"}


def _detect_subject(text: str) -> str | None:
    for triggers, subject in SUBJECT_HINTS:
        if any(re.search(r"\b" + re.escape(t.strip()) + r"\b", text) for t in triggers):
            return subject
    return None


def _detect_event(text: str):
    """Return (key, scene_template) for the first matching event, else (None, None)."""
    for key, triggers, template in EVENT_SCENES:
        if any(t in text for t in triggers):
            return key, template
    return None, None


def _detect_scene(text: str, subject: str | None) -> str:
    _, template = _detect_event(text)
    if template:
        if "{subject}" in template:
            return template.format(subject=subject or "a new tech product")
        return template
    if subject:
        return (f"a clean editorial product scene featuring {subject}, dramatic "
                f"studio lighting, modern Indonesian tech context")
    return DEFAULT_SCENE


def extract_entities(headline: str) -> list[str]:
    """Real-world brands/companies/places named in the headline, in display form."""
    low = headline.lower()
    found: list[str] = []
    for trigger, display in KNOWN_ENTITIES.items():
        if re.search(r"\b" + re.escape(trigger) + r"\b", low):
            if display not in found:
                found.append(display)
    # Drop an entity if it's contained in a more specific one (Samsung vs Samsung Galaxy)
    deduped = [e for e in found
               if not any(e != o and e in o for o in found)]
    return deduped[:4]


# Split only on real clause boundaries: comma+space, colon+space, or a spaced
# dash. This avoids breaking Indonesian decimals ("Rp1,5") and hyphenated words
# ("On-Device").
_CLAUSE_SPLIT = re.compile(r",\s+|:\s+|\s[–—-]\s")
_TAIL_STOPWORDS = {"di", "ke", "dari", "untuk", "dan", "yang", "buat", "atau",
                   "dengan", "ini", "itu", "the"}


def build_image_hook(headline: str) -> str:
    """Short, punchy, UPPERCASE headline to render on the image."""
    core = _CLAUSE_SPLIT.split(headline)[0].strip()
    words = core.split()
    if len(words) > 9:
        words = words[:9]
    while words and words[-1].lower() in _TAIL_STOPWORDS:
        words.pop()
    return " ".join(words).upper().strip()


def build_image_subtitle(headline: str, event_key: str | None) -> str:
    """A short supporting line rendered under the hook."""
    weak = {"ini dampaknya", "ini faktanya", "selengkapnya", "ini bocorannya",
            "ini penjelasannya", "begini ceritanya", "ini daftarnya", "cek di sini"}
    parts = _CLAUSE_SPLIT.split(headline, maxsplit=1)
    if len(parts) == 2:
        tail = parts[1].strip().rstrip(".")
        if 0 < len(tail.split()) <= 9 and tail.lower() not in weak:
            return tail
    return EVENT_SUBTITLE_ID.get(event_key, "Kabar teknologi terbaru Indonesia")


def build_image_prompt(story: dict) -> dict:
    """Return {prompt, hook, subtitle, entities} for the image."""
    headline = story["headline"]
    text = (headline + " " + " ".join(story.get("keywords", []))).lower()
    subject = _detect_subject(text)
    event_key, _ = _detect_event(text)
    scene = _detect_scene(text, subject)
    entities = extract_entities(headline)
    hook = build_image_hook(headline)
    subtitle = build_image_subtitle(headline, event_key)

    if entities:
        entity_line = (
            "Clearly and recognizably feature these REAL brands/products/places "
            f"so the audience instantly understands the story: {', '.join(entities)}. "
            "Show their real product likeness, logos and colors accurately. "
        )
    else:
        entity_line = ""

    prompt = (
        "Editorial tech-news poster, 1:1 square, social-media cover. "
        f"SCENE — depict this exact event: {scene}. "
        + entity_line +
        "TEXT ON IMAGE (render exactly, spelled correctly, no typos): "
        f"top bold UPPERCASE headline reading \"{hook}\"; "
        f"a smaller sub-headline below it reading \"{subtitle}\". "
        "Put the headline in the top third over a semi-transparent dark gradient "
        "banner for readability; keep the main visual in the lower two-thirds. "
        "Style: bold modern tech-magazine cover, cinematic lighting, high contrast, "
        "blue/cyan palette with a strong Indonesian red accent, clean sans-serif type. "
        "Do not depict real private individuals' faces. No watermarks. --ar 1:1"
    )
    return {"prompt": prompt, "hook": hook, "subtitle": subtitle, "entities": entities}


def _title_case_id(text: str) -> str:
    return text.strip().rstrip(".")


def build_caption(story: dict, lang: str = "id", style: str = "mix") -> str:
    """Caption styles:
    - hype: short, punchy, emoji-heavy (max reach)
    - explainer: hook + 'why it matters' (builds trust, saves/shares)
    - mix (default): hype hook + a short explainer payoff
    """
    headline = _title_case_id(story["headline"])
    n = story["article_count"]
    srcs = ", ".join(story["sources"][:3])

    if lang == "en":
        hook = f"🚨 TECH ALERT INDONESIA\n\n{headline}"
        why = (
            f"Why it matters: this is moving across {n} outlets ({srcs}) — a signal "
            f"worth watching for anyone in Indonesia's tech scene."
        )
        cta = "Save this 🔖 and follow for daily Indonesian tech & AI updates. "\
              "Your take? 👇"
    else:
        hook = f"🚨 KABAR TEKNO INDONESIA\n\n{headline}"
        why = (
            f"Kenapa penting: kabar ini dibahas di {n} media ({srcs}) — sinyal yang "
            f"layak dipantau buat kamu yang ngikutin dunia tech & AI Indonesia."
        )
        cta = "Simpan 🔖 & follow buat update teknologi tiap hari. "\
              "Menurut kamu gimana? 👇"

    if style == "hype":
        return f"{hook}\n\n{cta}"
    if style == "explainer":
        return f"{hook}\n\n{why}\n\n{cta}"
    # mix
    return f"{hook}\n\n{why}\n\n{cta}"


def build_hashtags(story: dict, limit: int = 12) -> list[str]:
    tags = list(HASHTAG_BASE)
    for kw in story["keywords"]:
        parts = [p for p in re.split(r"\s+", kw) if p and p.lower() not in _HASHTAG_SKIP]
        if not parts:
            continue
        # skip weak single words (too short / too generic)
        if len(parts) == 1 and len(parts[0]) < 4:
            continue
        tag = "#" + "".join(w.capitalize() for w in parts)
        if len(tag) > 3 and tag not in tags:
            tags.append(tag)
    return tags[:limit]


def make_posts(analysis: dict, cfg: dict) -> list[dict]:
    lang = cfg.get("caption_lang", "id")
    style = cfg.get("caption_style", "mix")
    top_n = cfg.get("top_stories", 8)
    posts = []
    for rank, story in enumerate(analysis["trending_stories"][:top_n], start=1):
        img = build_image_prompt(story)
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
                "image_prompt": img["prompt"],
                "image_hook": img["hook"],
                "image_subtitle": img["subtitle"],
                "image_entities": img["entities"],
                "caption": build_caption(story, lang, style),
                "hashtags": build_hashtags(story),
            }
        )
    return posts
