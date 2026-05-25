"""
Base scraper class with shared Playwright functionality for all platforms.
"""

from playwright.sync_api import sync_playwright, Page, Browser
import json
import os
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from config_helper import load_profile_config, copy_dir_incremental


class BaseScraper(ABC):
    """Base class for platform-specific scrapers."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        
        # Load profile configuration from config.json or OS defaults
        self.src_profile_dir, self.src_profile_name, self.use_real_profile = load_profile_config()

        if self.use_real_profile:
            # We copy to a temp directory to bypass Chrome's SingletonLock
            self.profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile-temp")
            self.profile_name = self.src_profile_name
        else:
            self.profile_dir = os.path.join(os.path.dirname(__file__), "chrome-profile")
            self.profile_name = None

        self.posted_posts_file = os.path.join(os.path.dirname(__file__), "posted_posts.json")
        self.comments_file = os.path.join(os.path.dirname(__file__), "comments.json")
        self.log_file = os.path.join(os.path.dirname(__file__), "scraper.log")

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        self._setup_logging()
        self._load_posted_posts()

    def _setup_logging(self):
        """Configure logging to file and console."""
        self.logger = logging.getLogger(self.platform_name)
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def _load_posted_posts(self):
        """Load the tracking file of posted comments."""
        if os.path.exists(self.posted_posts_file):
            with open(self.posted_posts_file, 'r') as f:
                self.posted_posts = json.load(f)
        else:
            self.posted_posts = {}

    def _save_posted_posts(self):
        """Save updated posted posts tracking."""
        with open(self.posted_posts_file, 'w') as f:
            json.dump(self.posted_posts, f, indent=2)

    def load_comments(self) -> list:
        """Load comment templates for this platform."""
        with open(self.comments_file, 'r') as f:
            all_comments = json.load(f)
        return all_comments.get(self.platform_name, [])

    def is_posted(self, post_id: str) -> bool:
        """Check if we've already commented on this post."""
        return post_id in self.posted_posts.get(self.platform_name, [])

    def mark_posted(self, post_id: str):
        """Mark a post as commented."""
        if self.platform_name not in self.posted_posts:
            self.posted_posts[self.platform_name] = []
        if post_id not in self.posted_posts[self.platform_name]:
            self.posted_posts[self.platform_name].append(post_id)
            self._save_posted_posts()

    def _prepare_temp_profile(self):
        """Clone the user's real profile (Profile 1) and Local State into a temp directory to bypass locks."""
        import shutil

        temp_profile_path = os.path.join(self.profile_dir, self.src_profile_name)
        
        # Create temp profile folder if not exists
        os.makedirs(temp_profile_path, exist_ok=True)

        # Copy Local State if it exists
        src_local_state = os.path.join(self.src_profile_dir, "Local State")
        if os.path.exists(src_local_state):
            try:
                shutil.copy2(src_local_state, os.path.join(self.profile_dir, "Local State"))
            except Exception as e:
                self.logger.warning(f"Failed to copy Local State: {e}")

        # Sync Profile 1 folder excluding caches/large files (cross-platform copy_dir_incremental)
        src_profile_path = os.path.join(self.src_profile_dir, self.src_profile_name)
        self.logger.info(f"Syncing profile {self.src_profile_name} to temporary directory...")
        try:
            copy_dir_incremental(
                src_profile_path,
                temp_profile_path,
                ["Cache*", "*Cache*", "Service Worker", "component_crx_cache"]
            )
        except Exception as e:
            self.logger.error(f"Failed to sync profile directory: {e}")

        # Delete any copied lock files to bypass the singleton lock
        for root, dirs, files in os.walk(self.profile_dir):
            for file in files:
                if "Singleton" in file or file == "LOCK":
                    try:
                        os.remove(os.path.join(root, file))
                    except OSError:
                        pass

    def launch_browser(self):
        """Launch persistent browser with existing profile."""
        if self.use_real_profile:
            self._prepare_temp_profile()
        else:
            os.makedirs(self.profile_dir, exist_ok=True)
            
        self.playwright = sync_playwright().start()
        
        launch_args = []
        if self.profile_name:
            launch_args.append(f"--profile-directory={self.profile_name}")
            
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=False,
            channel="chrome" if self.use_real_profile else None,
            args=launch_args,
        )
        self.browser = self.context.browser
        self.page = self.context.new_page()

    def close_browser(self):
        """Close the browser and stop playwright."""
        if self.page:
            try:
                self.page.close()
            except Exception:
                pass
            self.page = None
        if self.context:
            try:
                self.context.close()
            except Exception:
                pass
            self.context = None
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
            self.playwright = None

    def wait_for_selector(self, selector: str, timeout: int = 10000):
        """Wait for an element to be visible."""
        return self.page.wait_for_selector(selector, timeout=timeout)

    def click(self, selector: str):
        """Click an element."""
        self.page.click(selector)

    def type_text(self, selector: str, text: str):
        """Type text into an input field."""
        self.page.fill(selector, text)

    def get_text(self, selector: str) -> str:
        """Get text content of an element."""
        return self.page.text_content(selector)

    def submit(self, selector: str):
        """Submit a form."""
        self.page.click(selector)

    def go_to(self, url: str):
        """Navigate to a URL."""
        self.page.goto(url)

    def sleep(self, seconds: float):
        """Wait for a specified number of seconds."""
        import time
        time.sleep(seconds)

    def take_screenshot(self, name: str):
        """Take a screenshot and save to screenshots folder."""
        screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.platform_name}_{name}_{timestamp}.png"
        filepath = os.path.join(screenshots_dir, filename)
        self.page.screenshot(path=filepath, full_page=True)
        self.logger.info(f"Screenshot saved: {filename}")

    def run(self, num_comments: int = 3):
        """Run the scraper - to be implemented by subclasses."""
        try:
            self.launch_browser()
            self.logger.info(f"Starting {self.platform_name} scraper")
            comments_posted = 0

            posts = self.get_posts()
            for post in posts:
                if comments_posted >= num_comments:
                    break

                post_id = self.get_post_id(post)
                if self.is_posted(post_id):
                    self.logger.info(f"Skipping already posted post: {post_id}")
                    continue

                if not self.can_comment_on(post):
                    continue

                self.logger.info(f"Commenting on post: {post_id}")
                self.open_post(post)
                self.take_screenshot("post_opened")

                comments = self.load_comments()
                if comments:
                    comment = comments[comments_posted % len(comments)]
                    self.take_screenshot("before_typing")
                    self.post_comment(comment)
                    self.take_screenshot("after_typing")
                    self.sleep(2)

                    if self.verify_comment_posted():
                        self.mark_posted(post_id)
                        comments_posted += 1
                        self.logger.info(f"Successfully posted comment on {post_id}")
                    else:
                        self.logger.warning(f"Failed to verify comment on {post_id}")

                self.go_to(self.get_base_url())
                self.sleep(2)

            self.logger.info(f"Completed {self.platform_name}: {comments_posted} comments posted")
            return comments_posted

        except Exception as e:
            self.logger.error(f"Error in {self.platform_name} scraper: {str(e)}")
            return 0
        finally:
            self.close_browser()

    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL for this platform."""
        pass

    @abstractmethod
    def get_posts(self) -> list:
        """Scrape list of relevant posts."""
        pass

    @abstractmethod
    def get_post_id(self, post) -> str:
        """Extract unique identifier from a post."""
        pass

    @abstractmethod
    def can_comment_on(self, post) -> bool:
        """Check if we can comment on this post."""
        pass

    @abstractmethod
    def open_post(self, post):
        """Navigate to post detail page."""
        pass

    @abstractmethod
    def post_comment(self, comment: str):
        """Fill and submit comment form."""
        pass

    @abstractmethod
    def verify_comment_posted(self) -> bool:
        """Verify the comment appeared on the post."""
        pass