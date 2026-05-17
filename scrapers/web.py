"""
Playwright automation script - launches a persistent headed Chrome browser with a profile.
"""

from playwright.sync_api import sync_playwright
import os


def main():
    profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile")

    os.makedirs(profile_dir, exist_ok=True)

    playwright = sync_playwright().start()

    context = playwright.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
    )

    browser = context.browser

    print(f"Browser launched with profile at: {profile_dir}")
    print("Browser will stay open. Press Ctrl+C to exit.")

    try:
        input()
    except KeyboardInterrupt:
        print("\nClosing browser...")

    context.close()
    playwright.stop()


if __name__ == "__main__":
    main()