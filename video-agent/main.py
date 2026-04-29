#!/usr/bin/env python3
"""
Robotics Video Ideation Agent
-------------------------------
Run: python main.py

Workflow:
  1. Fetch trending robotics content (YouTube + TikTok)
  2. Claude generates 5-8 video ideas with YOUR unique angle
  3. You pick the ones you like
  4. Claude scripts them in your voice — streamed live
  5. Refine with feedback, save to disk
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Verify we're running from the right directory
if not Path("config/voice_profile.json").exists():
    print("Run from the video-agent/ directory: cd video-agent && python main.py")
    sys.exit(1)


def check_env():
    """Check required env vars and warn about missing optional ones."""
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY (required)")
    if not os.getenv("YOUTUBE_API_KEY"):
        print("  ⚠  YOUTUBE_API_KEY not set — YouTube trends disabled")
    if not os.getenv("TIKTOK_CLIENT_KEY") or not os.getenv("TIKTOK_CLIENT_SECRET"):
        print("  ⚠  TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET not set — TikTok trends disabled")
    if missing:
        print(f"\n  ✗ Missing required env vars: {', '.join(missing)}")
        print("  Copy .env.example to .env and fill in your keys.\n")
        sys.exit(1)


def pick_from_list(prompt: str, options: list[str], multi: bool = False) -> list[int]:
    """Simple numbered menu — no extra dependencies needed."""
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")

    if multi:
        raw = input("\nEnter numbers separated by commas (e.g. 1,3): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip()]
            return [i for i in indices if 0 <= i < len(options)]
        except ValueError:
            return []
    else:
        raw = input("\nEnter number: ").strip()
        try:
            i = int(raw) - 1
            return [i] if 0 <= i < len(options) else []
        except ValueError:
            return []


def step_fetch(days_back: int = 30) -> list[dict]:
    """Step 1: Fetch trends."""
    from agents.trend_fetcher import TrendFetcher

    print("\n" + "═" * 60)
    print("  STEP 1 — FETCH TRENDS")
    print("═" * 60)
    print(f"  Fetching robotics content from last {days_back} days...")

    fetcher = TrendFetcher()
    trends = fetcher.fetch_all(days_back=days_back)

    if not trends:
        print("\n  No trends found. Check your API keys in .env")
        sys.exit(1)

    print(f"\n  Total: {len(trends)} videos fetched")

    # Show platform breakdown
    by_platform: dict[str, int] = {}
    for t in trends:
        by_platform[t["platform"]] = by_platform.get(t["platform"], 0) + 1
    for platform, count in by_platform.items():
        print(f"    {platform}: {count} videos")

    return trends


def step_generate_ideas(trends: list[dict]) -> list[dict]:
    """Step 2: Generate ideas with Claude."""
    from agents.idea_generator import generate_ideas, display_ideas

    print("\n" + "═" * 60)
    print("  STEP 2 — GENERATING IDEAS")
    print("═" * 60)
    print("  Asking Claude to find your best angles...\n")

    ideas = generate_ideas(trends)
    display_ideas(ideas)
    return ideas


def step_pick_ideas(ideas: list[dict]) -> list[dict]:
    """Step 3: Creator picks which ideas to script."""
    titles = [f"#{i['rank']} {i['title']} ({i['pillar']})" for i in ideas]
    indices = pick_from_list(
        "Which ideas do you want to script? (pick one or more)",
        titles,
        multi=True,
    )
    if not indices:
        print("  Nothing selected. Exiting.")
        sys.exit(0)
    selected = [ideas[i] for i in indices]
    print(f"\n  Selected: {', '.join(s['title'] for s in selected)}")
    return selected


def step_script(ideas: list[dict]) -> None:
    """Step 4: Script each selected idea."""
    from agents.scriptwriter import write_script, refine_script, save_script

    for idea in ideas:
        print(f"\n\n{'═' * 60}")
        print(f"  SCRIPTING: {idea['title']}")
        print("═" * 60)

        # Optional: let creator add context
        extra = input("\n  Add any extra context or angle for this script? (Enter to skip): ").strip()

        script = write_script(idea, additional_context=extra)

        while True:
            print("\n  What would you like to do?")
            print("  1. Save this script")
            print("  2. Refine with feedback")
            print("  3. Regenerate from scratch")
            print("  4. Skip this idea")

            choice = input("\n  Enter number: ").strip()

            if choice == "1":
                path = save_script(idea, script)
                print(f"\n  ✓ Saved → {path}")
                break
            elif choice == "2":
                feedback = input("  Your feedback: ").strip()
                if feedback:
                    script = refine_script(script, feedback)
            elif choice == "3":
                extra2 = input("  Any different context? (Enter to skip): ").strip()
                script = write_script(idea, additional_context=extra2)
            elif choice == "4":
                print("  Skipped.")
                break
            else:
                print("  Enter 1, 2, 3, or 4.")


def load_latest_trends() -> list[dict]:
    """Load the most recent trends file instead of re-fetching."""
    data_dir = Path("data")
    trend_files = sorted(data_dir.glob("trends_*.json"), reverse=True)
    if not trend_files:
        return []
    with open(trend_files[0]) as f:
        trends = json.load(f)
    print(f"  Loaded {len(trends)} trends from {trend_files[0].name}")
    return trends


def main():
    print("\n" + "━" * 60)
    print("  ROBOTICS VIDEO IDEATION AGENT")
    print("━" * 60)

    check_env()

    # Offer to use cached trends if available
    data_dir = Path("data")
    trend_files = list(data_dir.glob("trends_*.json")) if data_dir.exists() else []

    use_cache = False
    if trend_files:
        latest = sorted(trend_files, reverse=True)[0]
        print(f"\n  Found cached trends: {latest.name}")
        choice = input("  Use cached trends? (Y/n): ").strip().lower()
        use_cache = choice != "n"

    if use_cache:
        trends = load_latest_trends()
    else:
        days_input = input("\n  How many days back to look? (default 30): ").strip()
        days_back = int(days_input) if days_input.isdigit() else 30
        trends = step_fetch(days_back=days_back)

    ideas = step_generate_ideas(trends)
    selected = step_pick_ideas(ideas)
    step_script(selected)

    print("\n" + "━" * 60)
    print("  Done! Scripts saved to data/scripts/")
    print("━" * 60 + "\n")


if __name__ == "__main__":
    main()
