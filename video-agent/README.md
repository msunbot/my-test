# Robotics Video Ideation Agent

Finds trending robotics topics, generates video ideas with your GS analyst + founder angle, and scripts them in your voice — for Instagram Reels.

## Setup

```bash
cd video-agent
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

## API Keys

| Key | Required | How to get |
|-----|----------|------------|
| `ANTHROPIC_API_KEY` | Yes | console.anthropic.com |
| `YOUTUBE_API_KEY` | Recommended | console.developers.google.com → enable YouTube Data API v3 |
| `TIKTOK_CLIENT_KEY` + `TIKTOK_CLIENT_SECRET` | Optional | developers.tiktok.com/products/research-api (approval takes a few days) |

YouTube alone is enough to get started.

## Run

```bash
python main.py
```

**Flow:**
1. Fetches trending robotics content from YouTube (+ TikTok if configured)
2. Claude generates 5-8 video ideas with your specific angle
3. You pick which ideas to script
4. Claude writes the script — streamed live to your terminal
5. Refine with feedback or save directly

Scripts are saved to `data/scripts/`.

## Customizing Your Voice

Edit `config/voice_profile.json` to adjust tone, audience, style rules.
Edit `config/content_pillars.json` to add/remove topic buckets.
Edit `config/keywords.json` to add companies or keywords you're tracking.

## File Structure

```
video-agent/
├── main.py                    # Run this
├── config/
│   ├── voice_profile.json     # Your persona, style, audience
│   ├── content_pillars.json   # 7 robotics topic buckets
│   └── keywords.json          # Keywords + companies to track
├── agents/
│   ├── trend_fetcher.py       # YouTube + TikTok data
│   ├── idea_generator.py      # Claude idea generation
│   └── scriptwriter.py        # Claude script writing (streaming)
└── data/
    ├── trends_*.json          # Cached trend data
    └── scripts/               # Your saved scripts
```
