"""Quick check to see if sites load and if logged in."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.sync_api import sync_playwright


def check_sites():
    profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
        )
        page = context.new_page()

        sites = [
            ("IndieHackers", "https://www.indiehackers.com"),
            ("Dev.to", "https://dev.to"),
            ("Quora", "https://www.quora.com"),
            ("Uneed", "https://uneed.best"),
            ("BetaList", "https://betalist.com"),
            ("HackerNews", "https://news.ycombinator.com"),
        ]

        for name, url in sites:
            print(f"\n=== {name} ===")
            try:
                page.goto(url, timeout=15000)
                page.wait_for_load_state(timeout=10000)
                print(f"URL: {page.url}")
                print(f"Title: {page.title()[:100]}")

                # Check for login/greeting elements
                body = page.content()[:5000]
                if "sign in" in body.lower() or "login" in body.lower():
                    print("Status: May need login")
                else:
                    print("Status: Page loaded")

            except Exception as e:
                print(f"Error: {str(e)[:100]}")

        input("\nPress Enter to close...")
        context.close()


if __name__ == "__main__":
    check_sites()