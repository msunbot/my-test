# Robotics & Supply Chain News Aggregator

Pulls from 16 RSS feeds (8 Chinese, 8 English), triages with Claude Haiku, then runs a deep analysis + social-post draft with Claude Opus for every high-relevance article.

## Sources

**Chinese** — 36Kr, Huxiu, TMTPost, Jiqizhixin, Leiphone, Jiemian, ThePaper, Caixin  
**English** — Reuters Tech, SCMP, Nikkei Asia, TechCrunch, IEEE Spectrum, The Robot Report, Wired, Rest of World

## Setup

```bash
cd robotics-news-aggregator
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then add your key
```

## Usage

```bash
# Print digest to terminal (one-shot)
python main.py

# Save digest + social posts to digests/ directory
python main.py --save

# Show only the compact social-post copy-paste block
python main.py --social

# Continuous mode — runs every 6 hours, saves each digest
python main.py --schedule --save

# Skip full-text scraping (faster, lower quality)
python main.py --no-full-text

# Increase article cap (default 30)
python main.py --max-articles 50

# Verbose logging
python main.py -v
```

## Output per article

Each article the model deems relevant (score ≥ 6/10) gets:

| Field | Description |
|---|---|
| `headline` | Punchy English headline ≤12 words |
| `summary_en` | 2-3 sentence English summary |
| `key_facts` | 3-5 specific facts, numbers, names |
| `why_it_matters` | Analyst take on industry implications |
| `x_post` | Tweet ≤280 chars, no hashtags, 1-2 emojis |
| `linkedin_post` | 150-250 word post ending with engagement question |
| `video_hook` | 1-2 sentence spoken hook for a 90-sec video |
| `video_outline` | 4-5 talking-point bullets for the video body |
| `tags` | 3-5 topic tags |

## Cost model

- **Haiku** scores every candidate article (cheap — typically $0.001–0.003 per run)
- **Opus** only runs on articles scoring ≥ 6, with adaptive thinking + prompt caching
- The stable system prompt is cached across all calls in a run, cutting repeat-token costs ~90%

## Customization

| What | Where |
|---|---|
| Add/remove RSS sources | `config.py` → `ALL_SOURCES` |
| Adjust keyword filter | `config.py` → `KEYWORDS` |
| Change triage threshold | `processor.py` → `triage_articles()`, line `if score >= 6` |
| Change fetch cadence | `config.py` → `FETCH_INTERVAL_HOURS` |
| Change article cap | `config.py` → `MAX_ARTICLES_PER_RUN` |
| Tweak Opus prompt / schema | `processor.py` → `_ANALYSIS_SCHEMA` and `analyze_article()` |
| Change digest format | `formatter.py` |
