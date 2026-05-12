"""
Format the analysis output into Markdown digests and platform-specific posts.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional

from fetcher import Article


def _divider(char: str = "─", width: int = 60) -> str:
    return char * width


def format_article_block(art: Article, analysis: dict, idx: int) -> str:
    """Format one article + its analysis as a Markdown section."""
    lines = [
        f"\n## {idx}. {analysis.get('headline', art.title)}",
        f"**Source:** {art.source_name}  ·  **Lang:** {art.lang.upper()}  ·  **Score:** {art.relevance_score:.0f}/10",
        f"**URL:** {art.url}",
        "",
        "### Summary",
        analysis.get("summary_en", art.summary),
        "",
        "### Key Facts",
    ]
    for fact in analysis.get("key_facts", []):
        lines.append(f"- {fact}")

    lines += [
        "",
        "### Why It Matters",
        analysis.get("why_it_matters", ""),
        "",
        _divider("─", 40),
        "",
        "### 𝕏 Post",
        "```",
        analysis.get("x_post", ""),
        "```",
        "",
        "### LinkedIn Post",
        analysis.get("linkedin_post", ""),
        "",
        "### 🎬 Video Hook",
        f"> {analysis.get('video_hook', '')}",
        "",
        "### Video Talking Points",
    ]
    for point in analysis.get("video_outline", []):
        lines.append(f"- {point}")

    tags = " · ".join(f"`{t}`" for t in analysis.get("tags", []))
    lines += ["", f"**Tags:** {tags}", "", _divider("═", 60)]
    return "\n".join(lines)


def format_digest(
    articles: list[Article],
    analyses: list[Optional[dict]],
    intro: str = "",
    run_ts: Optional[str] = None,
) -> str:
    """Build the full Markdown digest document."""
    if run_ts is None:
        run_ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    header = [
        f"# 🤖 Robotics & Supply Chain Digest",
        f"**Generated:** {run_ts}",
        "",
    ]
    if intro:
        header += ["## Editorial Overview", intro, "", _divider("═", 60)]

    blocks = []
    n = 0
    for art, analysis in zip(articles, analyses):
        if analysis:
            n += 1
            blocks.append(format_article_block(art, analysis, n))

    if not blocks:
        blocks = ["*No relevant articles found this run.*"]

    return "\n".join(header + blocks)


def save_digest(content: str, output_dir: str = "digests") -> Path:
    """Write digest to a timestamped Markdown file."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M")
    file_path = path / f"digest_{ts}.md"
    file_path.write_text(content, encoding="utf-8")
    return file_path


def format_social_batch(
    articles: list[Article],
    analyses: list[Optional[dict]],
) -> str:
    """Compact view of just the social posts, for quick copy-paste."""
    lines = ["# Social Media Posts — Quick Reference", ""]
    n = 0
    for art, analysis in zip(articles, analyses):
        if not analysis:
            continue
        n += 1
        lines += [
            f"## [{n}] {analysis.get('headline', art.title)}",
            f"Source: {art.source_name}  |  {art.url}",
            "",
            "**𝕏:**",
            analysis.get("x_post", ""),
            "",
            "**LinkedIn:**",
            analysis.get("linkedin_post", ""),
            "",
            "**Video hook:**",
            analysis.get("video_hook", ""),
            "",
            _divider("─", 50),
            "",
        ]
    return "\n".join(lines)
