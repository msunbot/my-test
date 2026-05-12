"""
Robotics & Supply Chain News Aggregator
========================================
Run modes:
  python main.py            – single run, print digest to stdout
  python main.py --save     – single run, save digest to digests/ directory
  python main.py --schedule – continuous scheduled runs every N hours
  python main.py --social   – print compact social-post quick-reference
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from config import (
    ALL_SOURCES, FETCH_INTERVAL_HOURS, MAX_ARTICLES_PER_RUN,
    OUTPUT_DIR, DB_PATH,
)
from fetcher import fetch_all_sources, fetch_full_text, Article
from processor import triage_articles, translate_article, analyze_article, generate_digest_intro
from formatter import format_digest, format_social_batch, save_digest
from storage import ArticleStore

load_dotenv()
console = Console()
log = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore", "feedparser", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def run_pipeline(
    store: ArticleStore,
    max_articles: int = MAX_ARTICLES_PER_RUN,
    fetch_full: bool = True,
) -> tuple[list[Article], list[dict | None], str, str]:
    """
    Full pipeline: fetch → triage → translate → analyze → format.
    Returns (articles, analyses, digest_md, social_md).
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:

        # 1. Fetch
        task = progress.add_task("Fetching RSS feeds…", total=None)
        candidates = fetch_all_sources(ALL_SOURCES)
        progress.update(task, description=f"Fetched {len(candidates)} candidates")

        # 2. Filter already-seen
        task2 = progress.add_task("Filtering seen articles…", total=None)
        fresh = [a for a in candidates if not store.is_seen(a.url)]
        progress.update(task2, description=f"{len(fresh)} new articles")

        if not fresh:
            console.print("[yellow]No new articles found.[/yellow]")
            return [], [], "No new articles.", "No new articles."

        # 3. Triage with Haiku
        task3 = progress.add_task("Triaging with Haiku…", total=None)
        relevant = triage_articles(fresh)[:max_articles]
        progress.update(task3, description=f"{len(relevant)} relevant articles after triage")

        # 4. Mark seen early so concurrent runs don't re-process
        for art in relevant:
            store.mark_seen(art.url)

        # 5. Translate Chinese articles + optionally fetch full text
        task4 = progress.add_task("Translating & fetching full text…", total=None)
        for art in relevant:
            if art.lang == "zh":
                try:
                    art.translation = translate_article(art)
                except Exception as exc:
                    log.warning("Translation failed: %s", exc)
            if fetch_full:
                art.full_text = fetch_full_text(art.url)
        progress.update(task4, description="Done")

        # 6. Deep analysis with Opus
        task5 = progress.add_task("Analyzing with Opus…", total=None)
        analyses: list[dict | None] = []
        for i, art in enumerate(relevant):
            progress.update(task5, description=f"Analyzing {i+1}/{len(relevant)}…")
            analyses.append(analyze_article(art))
        progress.update(task5, description="Analysis complete")

        # 7. Digest intro
        good_analyses = [a for a in analyses if a]
        intro = ""
        if good_analyses:
            task6 = progress.add_task("Writing editorial intro…", total=None)
            intro = generate_digest_intro(relevant, analyses)
            progress.update(task6, description="Done")

    digest_md = format_digest(relevant, analyses, intro=intro)
    social_md = format_social_batch(relevant, analyses)
    return relevant, analyses, digest_md, social_md


def single_run(args, store: ArticleStore):
    articles, analyses, digest_md, social_md = run_pipeline(
        store,
        max_articles=args.max_articles,
        fetch_full=not args.no_full_text,
    )

    if args.social:
        console.print(Markdown(social_md))
    else:
        console.print(Markdown(digest_md))

    if args.save:
        path = save_digest(digest_md, OUTPUT_DIR)
        console.print(f"\n[green]Digest saved → {path}[/green]")
        social_path = path.with_name(path.stem + "_social.md")
        social_path.write_text(social_md, encoding="utf-8")
        console.print(f"[green]Social posts → {social_path}[/green]")

        if articles:
            store.save_digest(digest_md)

    return articles, analyses


def scheduled_run(args, store: ArticleStore):
    console.print(f"[bold cyan]Scheduler started — running every {FETCH_INTERVAL_HOURS}h[/bold cyan]")

    def _job():
        console.rule(f"[bold]Run @ {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}[/bold]")
        single_run(args, store)

    _job()   # run immediately
    schedule.every(FETCH_INTERVAL_HOURS).hours.do(_job)
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(
        description="Robotics & Supply Chain News Aggregator powered by Claude"
    )
    parser.add_argument("--save",           action="store_true", help="Save digest to file")
    parser.add_argument("--schedule",       action="store_true", help="Run continuously on a schedule")
    parser.add_argument("--social",         action="store_true", help="Show compact social posts only")
    parser.add_argument("--no-full-text",   action="store_true", help="Skip full-text scraping")
    parser.add_argument("--max-articles",   type=int, default=MAX_ARTICLES_PER_RUN)
    parser.add_argument("--verbose", "-v",  action="store_true")
    parser.add_argument("--db",             default=DB_PATH, help="SQLite DB path")
    args = parser.parse_args()

    setup_logging(args.verbose)

    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY not set. Add it to .env or export it.[/red]")
        sys.exit(1)

    store = ArticleStore(args.db)
    try:
        if args.schedule:
            scheduled_run(args, store)
        else:
            single_run(args, store)
    finally:
        store.close()


if __name__ == "__main__":
    main()
