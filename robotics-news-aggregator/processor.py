"""
Claude-powered processing pipeline.

Two-tier strategy:
  1. Haiku  — fast relevance triage (cheap, runs on every candidate)
  2. Opus   — deep analysis + social post drafting (only for top articles)

Prompt caching is used on the stable system prompt to reduce cost on repeated runs.
"""
import json
import logging
from typing import Optional

import anthropic

from config import HAIKU_MODEL, OPUS_MODEL
from fetcher import Article

log = logging.getLogger(__name__)

client = anthropic.Anthropic()

# ── Shared system prompt (cached) ─────────────────────────────────────────────
_SYSTEM_PROMPT = """\
You are an expert analyst covering the Chinese and global robotics and supply chain industries.
You have deep knowledge of:
- Chinese robotics companies: Unitree (宇树), UBTECH (优必选), Fourier Intelligence (傅利叶), Agibot (智元), Leju (乐聚), Dreame, Xiaomi robots
- Global robotics: Boston Dynamics, Figure AI, Agility Robotics, 1X, Apptronik, ABB, FANUC, Yaskawa
- Supply chain dynamics: US-China tech decoupling, semiconductor export controls, TSMC, SMIC, Huawei
- Industry trends: humanoid robots, embodied AI (具身智能), factory automation, EV supply chains

You help create content for a newsletter/social media account with English-speaking audiences \
interested in Chinese tech + robotics. Posts should be insightful, opinionated, and specific—\
not generic summaries. The author's voice is analytical, data-driven, occasionally provocative.

Always respond in valid JSON unless explicitly instructed otherwise.
"""

# ── Haiku: triage ─────────────────────────────────────────────────────────────

def triage_articles(articles: list[Article]) -> list[Article]:
    """
    Use Haiku to score each article's relevance (0-10).
    Returns only articles scoring >= 6, sorted descending.
    Prompt caching on the system block reduces cost after first call.
    """
    scored: list[tuple[float, Article]] = []

    for art in articles:
        prompt = (
            f"Source: {art.source_name} ({art.lang})\n"
            f"Title: {art.title}\n"
            f"Summary: {art.summary[:600]}\n\n"
            "Score this article's relevance to Chinese robotics and/or supply chain on a 0-10 scale.\n"
            "Respond ONLY with JSON: {\"score\": <int>, \"reason\": \"<15 words max>\"}"
        )

        try:
            resp = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=128,
                system=[{
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # cached after first call
                }],
                messages=[{"role": "user", "content": prompt}],
            )
            data = json.loads(resp.content[0].text)
            score = float(data.get("score", 0))
            art.relevance_score = score
            if score >= 6:
                scored.append((score, art))
                log.debug("Score %.0f  %s", score, art.title[:60])
        except Exception as exc:
            log.warning("Triage failed for '%s': %s", art.title[:50], exc)

    scored.sort(reverse=True, key=lambda t: t[0])
    return [art for _, art in scored]


# ── Opus: translation ─────────────────────────────────────────────────────────

def translate_article(art: Article) -> str:
    """Translate a Chinese article's title+summary into English."""
    content = f"Title: {art.title}\n\nSummary: {art.summary}"
    resp = client.messages.create(
        model=HAIKU_MODEL,   # translation doesn't need Opus
        max_tokens=512,
        system=[{
            "type": "text",
            "text": _SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": (
                "Translate the following Chinese tech news into fluent English. "
                "Keep proper nouns, company names, and numbers exact.\n\n"
                + content
            ),
        }],
    )
    return resp.content[0].text.strip()


# ── Opus: deep analysis + content generation ──────────────────────────────────

_ANALYSIS_SCHEMA = {
    "headline":       "str  – punchy English headline (≤12 words)",
    "summary_en":     "str  – 2-3 sentence English summary",
    "key_facts":      "list[str]  – 3-5 specific facts, numbers, names",
    "why_it_matters": "str  – 2-3 sentence analyst take: implications for the industry",
    "x_post":         "str  – tweet ≤280 chars, no hashtags, punchy opener, end with 1-2 relevant emojis",
    "linkedin_post":  "str  – 150-250 word LinkedIn post, professional but opinionated, one bold claim, end with a question to drive comments",
    "video_hook":     "str  – 1-2 sentence hook for a 90-sec talking-head video (grabby, spoken aloud)",
    "video_outline":  "list[str]  – 4-5 bullet talking points for the video body",
    "tags":           "list[str]  – 3-5 topic tags (e.g. humanoids, supply-chain, TSMC)",
}

def analyze_article(art: Article) -> Optional[dict]:
    """
    Full Opus analysis + social post drafts for a single high-relevance article.
    Returns a dict matching _ANALYSIS_SCHEMA, or None on failure.
    """
    # Build context – prefer full_text > summary
    body = art.full_text or art.summary
    lang_note = "The article is in Chinese." if art.lang == "zh" else ""
    translation_note = (
        f"\n\nPre-translated title: {art.translation}" if art.translation else ""
    )

    user_msg = (
        f"Analyze this article and produce ALL fields below in JSON.\n\n"
        f"Source: {art.source_name}  |  URL: {art.url}\n"
        f"Title: {art.title}\n"
        f"{lang_note}{translation_note}\n\n"
        f"Article body:\n{body[:3000]}\n\n"
        "Required JSON schema:\n"
        + json.dumps(_ANALYSIS_SCHEMA, ensure_ascii=False, indent=2)
    )

    try:
        resp = client.messages.create(
            model=OPUS_MODEL,
            max_tokens=2048,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            system=[{
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_msg}],
        )

        # Extract text block (thinking blocks come first when adaptive thinking fires)
        text = next(
            (b.text for b in resp.content if b.type == "text"), ""
        )

        # Strip markdown code fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.rsplit("```", 1)[0]

        return json.loads(text)

    except Exception as exc:
        log.error("Analysis failed for '%s': %s", art.title[:50], exc)
        return None


# ── Digest summary ────────────────────────────────────────────────────────────

def generate_digest_intro(articles: list[Article], analyses: list[dict]) -> str:
    """Generate a short editorial intro for the full digest using Opus."""
    headlines = "\n".join(
        f"- {a.get('headline', art.title)}"
        for art, a in zip(articles, analyses)
        if a
    )
    resp = client.messages.create(
        model=OPUS_MODEL,
        max_tokens=512,
        system=[{
            "type": "text",
            "text": _SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        messages=[{
            "role": "user",
            "content": (
                "Write a 3-4 sentence editorial intro for a robotics/supply-chain digest. "
                "Identify the 1-2 dominant themes across these stories. Be specific and opinionated.\n\n"
                "Stories:\n" + headlines
            ),
        }],
    )
    return resp.content[0].text.strip()
