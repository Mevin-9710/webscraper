"""
Main orchestrator for running all platform scrapers sequentially.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers import (
    IndieHackersScraper,
    DevtoScraper,
    QuoraScraper,
    UneedScraper,
    HackerNewsScraper,
    BlueskyScraper,
    SubstackScraper,
)
from datetime import datetime


def run_all_scrapers(num_comments_per_platform: int = 3, exclude_list: list = None):
    """Run all platform scrapers sequentially."""
    if exclude_list is None:
        exclude_list = []
    scrapers = [
        IndieHackersScraper("indiehackers"),
        DevtoScraper("devto"),
        QuoraScraper("quora"),
        UneedScraper("uneed"),
        HackerNewsScraper("hackernews"),
        BlueskyScraper("bluesky"),
        SubstackScraper("substack"),
    ]

    total_comments = 0
    results = []

    print("=" * 60)
    print(f"Rixly Promotion Bot - Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for scraper in scrapers:
        platform = scraper.platform_name
        if platform in exclude_list:
            print(f"[SKIP] {platform} (excluded)")
            continue
        print(f"\n[START] Running {platform} scraper...")

        try:
            comments_posted = scraper.run(num_comments_per_platform)
            total_comments += comments_posted

            results.append({
                'platform': platform,
                'success': True,
                'comments': comments_posted
            })
            print(f"[DONE] {platform}: {comments_posted} comments posted")

        except Exception as e:
            print(f"[ERROR] {platform} scraper failed: {str(e)}")
            results.append({
                'platform': platform,
                'success': False,
                'error': str(e),
                'comments': 0
            })

    print("\n" + "=" * 60)
    print("SUMMARY REPORT")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total comments posted: {total_comments}")
    print("\nPlatform results:")
    for result in results:
        status = "OK" if result['success'] else "FAILED"
        print(f"  - {result['platform']}: {result['comments']} comments ({status})")
    print("=" * 60)

    return total_comments


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Rixly promotion bot across all platforms")
    parser.add_argument(
        '--comments',
        type=int,
        default=3,
        help='Number of comments to post per platform (default: 3)'
    )
    parser.add_argument(
        '--platform',
        type=str,
        default=None,
        help='Run only a specific platform (indiehackers, devto, quora, uneed, hackernews, bluesky, substack)'
    )

    parser.add_argument(
        '--exclude',
        type=str,
        default=None,
        help='Comma-separated platforms to exclude (e.g., "substack,quora")'
    )

    args = parser.parse_args()

    exclude_list = args.exclude.split(',') if args.exclude else []
    exclude_list = [p.strip() for p in exclude_list]

    if args.platform:
        # Run only specific platform
        platform_map = {
            'indiehackers': IndieHackersScraper,
            'devto': DevtoScraper,
            'quora': QuoraScraper,
            'uneed': UneedScraper,
            'hackernews': HackerNewsScraper,
            'bluesky': BlueskyScraper,
            'substack': SubstackScraper,
        }
        if args.platform not in platform_map:
            print(f"Unknown platform: {args.platform}")
            print(f"Available: {', '.join(platform_map.keys())}")
            sys.exit(1)

        print(f"Running only {args.platform}...")
        scraper_class = platform_map[args.platform]
        scraper = scraper_class(args.platform)
        comments = scraper.run(args.comments)
        print(f"{args.platform}: {comments} comments posted")
    else:
        run_all_scrapers(args.comments, exclude_list)