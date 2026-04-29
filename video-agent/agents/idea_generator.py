"""
Idea generator: takes raw trend data and your voice profile,
asks Claude to identify the 5-8 most compelling video opportunities
with your specific angle for each one.
"""

import json
import os
import anthropic


IDEA_SYSTEM_PROMPT = """You are a video ideation assistant for a robotics content creator with this exact background:

CREATOR PROFILE:
- Former Goldman Sachs tech analyst (deep finance + investment lens)
- Pre-funding robotics founder (operator who knows what's actually hard to build)
- Audience: (1) career seekers wanting into robotics, (2) curious tech-forward general public
- Style: Zauey.talks structure (accessible hooks, friend-explaining-over-coffee energy) + Hope depth (technical rigor, financial substance)
- Platform: Instagram Reels, ~75 seconds, ~180 words

YOUR JOB:
Given trending robotics content, identify the most compelling video opportunities. For each idea, find the angle ONLY this creator can give — where their GS background + founder experience + technical understanding creates unique insight the average tech creator can't.

OUTPUT FORMAT — return a JSON array with this exact structure:
[
  {
    "rank": 1,
    "title": "Short title for the idea (6-10 words)",
    "pillar": "funding|hardware|career|explainer|implications|founder|ai_x_robotics",
    "hook": "The exact opening line — drop them in mid-thought, no intro",
    "unique_angle": "What makes YOUR take different from every other robotics creator covering this",
    "why_now": "Why this topic is hot RIGHT NOW based on the trends",
    "target_viewer": "career_seeker|general_public|both",
    "estimated_virality": "high|medium",
    "source_videos": ["title of trend that inspired this"]
  }
]

Return 5-8 ideas ranked by potential impact. Prioritize ideas where the creator's unique lens (GS + founder) adds real differentiation. No filler ideas."""


def generate_ideas(trends: list[dict], n_ideas: int = 8) -> list[dict]:
    """
    Send trend data to Claude and get back ranked video ideas.
    Uses adaptive thinking for better ideation quality.
    Uses prompt caching on the system prompt (it never changes per run).
    """
    client = anthropic.Anthropic()

    with open("config/content_pillars.json") as f:
        pillars = json.load(f)

    # Condense trend data for the prompt — keep top 30 by views
    top_trends = sorted(trends, key=lambda x: x.get("view_count", 0), reverse=True)[:30]
    trend_summary = []
    for t in top_trends:
        trend_summary.append({
            "platform": t["platform"],
            "title": t["title"][:120],
            "views": t.get("view_count", 0),
            "likes": t.get("like_count", 0),
            "keyword": t.get("search_keyword", t.get("hashtags", [""])[0] if t.get("hashtags") else ""),
        })

    pillar_names = [p["name"] for p in pillars["pillars"]]

    user_message = f"""Here are trending robotics videos from the last 30 days (sorted by views):

{json.dumps(trend_summary, indent=2)}

Available content pillars: {', '.join(pillar_names)}

Generate {n_ideas} video ideas with the creator's unique GS analyst + robotics founder angle.
Return ONLY the JSON array, no other text."""

    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": IDEA_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # cache the system prompt
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    )

    # Extract text from response (thinking blocks come first, skip them)
    raw_text = ""
    for block in response.content:
        if block.type == "text":
            raw_text = block.text
            break

    # Parse JSON — Claude should return clean JSON but strip markdown fences if present
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip().rstrip("```")

    ideas = json.loads(raw_text)
    return ideas


def display_ideas(ideas: list[dict]) -> None:
    """Pretty-print the ideas for the user to review."""
    print("\n" + "═" * 60)
    print("  VIDEO IDEAS — ranked by potential")
    print("═" * 60)

    for idea in ideas:
        virality_marker = "🔥" if idea.get("estimated_virality") == "high" else "📈"
        print(f"\n{virality_marker}  #{idea['rank']} — {idea['title']}")
        print(f"   Pillar: {idea['pillar']}  |  For: {idea.get('target_viewer', 'both')}")
        print(f"   Hook:   \"{idea['hook']}\"")
        print(f"   Angle:  {idea['unique_angle']}")
        print(f"   Why now: {idea['why_now']}")
        print()
