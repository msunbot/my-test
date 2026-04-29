"""
Script writer: takes a selected idea and generates a full short-form video script
in the creator's voice. Streams output so you see it as Claude writes it.
"""

import json
import os
import anthropic


SCRIPT_SYSTEM_PROMPT = """You write Instagram Reel scripts for a specific creator. Here is everything you need to know about them:

WHO THEY ARE:
- Former Goldman Sachs tech analyst — they understand how capital flows, what valuations signal, how to read a fundraise
- Pre-funding robotics founder — they know the unglamorous reality behind the demos: the supply chain issues, the hiring market, what's actually hard to build
- They're in the arena, not just commenting from the sideline

THEIR AUDIENCE:
- Primary: Smart people who want careers in robotics (engineers, PMs, finance people looking to pivot)
- Secondary: Curious, tech-forward general public who want to feel ahead of the curve
- Both groups: Smart. Don't talk down to them.

FORMAT: Instagram Reel, ~75 seconds when read aloud, ~170-190 words

STRUCTURE:
1. HOOK (0-5s): Drop in mid-thought. Bold statement or surprising fact. No "Hey everyone", no "Today I want to talk about". Start with the point.
2. CONTEXT (5-20s): Why this matters NOW. The news, the event, the number that makes it timely.
3. INSIGHT (20-65s): Your unique angle. The GS lens (follow the money). The founder lens (what's actually hard). The technical truth (what's really happening under the hood). This is where you differentiate.
4. CLOSE (65-75s): One question or provocative statement that makes them think. NOT "follow me for more".

VOICE RULES (follow these strictly):
- Short sentences. Like this. Not academic.
- Concrete: company names, dollar figures, specific years/dates — not vague gestures at "the industry"
- First person: your opinion, your take, your experience
- Accessible but never condescending
- No "guys", no "Hey everyone", no "In today's video"
- Speak directly to one person, not a crowd
- End on something that makes them think or feel something — not a follow request

OUTPUT FORMAT:
Return the script with this exact structure:

---HOOK---
[hook text]

---CONTEXT---
[context text]

---INSIGHT---
[insight text]

---CLOSE---
[close text]

---FULL SCRIPT---
[complete script as it would be read aloud, no section headers]

---NOTES---
[1-2 sentences on delivery: pace, emphasis, energy level]
[Word count: X words | ~Y seconds]"""


def write_script(idea: dict, additional_context: str = "") -> str:
    """
    Stream a script for the selected idea.
    Returns the full script text when done.
    """
    client = anthropic.Anthropic()

    user_message = f"""Write a script for this video idea:

TITLE: {idea['title']}
PILLAR: {idea['pillar']}
HOOK TO OPEN WITH: {idea['hook']}
UNIQUE ANGLE: {idea['unique_angle']}
WHY NOW: {idea['why_now']}
TARGET VIEWER: {idea.get('target_viewer', 'both')}

{f"ADDITIONAL CONTEXT: {additional_context}" if additional_context else ""}

Write the full script now. Follow the format exactly. Make it sound like the creator speaking — not like content."""

    print("\n" + "─" * 60)
    print("  WRITING SCRIPT...")
    print("─" * 60 + "\n")

    full_script = ""

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=2048,
        thinking={"type": "adaptive"},
        system=[
            {
                "type": "text",
                "text": SCRIPT_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for event in stream:
            if event.type == "content_block_start":
                # Skip thinking blocks silently
                pass
            elif event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    text = event.delta.text
                    print(text, end="", flush=True)
                    full_script += text

    print("\n\n" + "─" * 60)
    return full_script


def save_script(idea: dict, script: str) -> str:
    """Save script to disk and return filepath."""
    os.makedirs("data/scripts", exist_ok=True)
    safe_title = idea["title"].lower().replace(" ", "_")[:40]
    from datetime import datetime
    filename = f"data/scripts/{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}.md"

    content = f"""# {idea['title']}

**Pillar:** {idea['pillar']}
**Hook:** {idea['hook']}
**Unique Angle:** {idea['unique_angle']}

---

{script}
"""
    with open(filename, "w") as f:
        f.write(content)
    return filename


def refine_script(script: str, feedback: str) -> str:
    """Refine an existing script based on creator feedback. Streams output."""
    client = anthropic.Anthropic()

    print("\n" + "─" * 60)
    print("  REFINING SCRIPT...")
    print("─" * 60 + "\n")

    full_script = ""

    with client.messages.stream(
        model="claude-opus-4-7",
        max_tokens=2048,
        system=[
            {
                "type": "text",
                "text": SCRIPT_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Here is the current script:\n\n{script}\n\nCreator feedback: {feedback}\n\nRewrite the full script incorporating this feedback. Keep the same structure and format.",
            }
        ],
    ) as stream:
        for event in stream:
            if event.type == "content_block_delta":
                if hasattr(event.delta, "text"):
                    text = event.delta.text
                    print(text, end="", flush=True)
                    full_script += text

    print("\n\n" + "─" * 60)
    return full_script
