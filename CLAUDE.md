# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a browser automation tool for posting promotional comments across multiple platforms. It uses Playwright with a persistent Chrome profile to maintain login sessions and automate comment posting.

## Commands

```bash
# Run all platform scrapers (3 comments per platform by default)
python bot.py

# Run with custom number of comments per platform
python bot.py --comments 5

# Run only a specific platform
python bot.py --platform devto
python bot.py --platform indiehackers
python bot.py --platform quora
python bot.py --platform uneed
python bot.py --platform hackernews

# Check login status across all sites
python check_login.py
```

## Architecture

**Base Class ([base_scraper.py](base_scraper.py))**: Abstract base class providing Playwright browser automation, logging, and tracking. Subclasses implement platform-specific logic.

**Scrapers ([scrapers/](scrapers/))**: Platform-specific implementations that inherit from BaseScraper:
- `indiehackers.py` - IndieHackers.com
- `devto.py` - Dev.to
- `quora.py` - Quora
- `uneed.py` - Uneed.best
- `betalist.py` - BetaList
- `hackernews.py` - Hacker News

**Orchestrator ([bot.py](bot.py))**: Runs all scrapers sequentially and reports results.

**Data Files**:
- `comments.json` - Comment templates per platform
- `posted_posts.json` - Tracks which posts have been commented on
- `chrome-profile/` - Persistent Chrome profile for login state
- `screenshots/` - Debug screenshots captured during execution
- `scraper.log` - Execution logs

The scraper uses headful Chrome (headless=False) to allow manual interaction if needed.