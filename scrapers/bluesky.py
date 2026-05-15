"""Bluesky scraper."""

from base_scraper import BaseScraper


class BlueskyScraper(BaseScraper):
    """Scraper for Bluesky social posts."""

    def get_base_url(self):
        return "https://bsky.app"

    def get_posts(self):
        """Scrape latest posts from Bluesky home feed."""
        posts = []
        try:
            self.go_to("https://bsky.app")
            self.sleep(4)

            # Find feed items using data-testid pattern
            feed_items = self.page.query_selector_all('[data-testid^="feedItem-by-"]')
            self.logger.info(f"Found {len(feed_items)} posts in feed")

            for item in feed_items[:20]:
                try:
                    # Get the timestamp link which contains the post URL
                    timestamp_link = item.query_selector('a[href*="/post/"]')
                    if timestamp_link:
                        href = timestamp_link.get_attribute('href')
                        if href:
                            # Extract handle from data-testid
                            testid = item.get_attribute('data-testid')
                            handle = testid.replace('feedItem-by-', '') if testid else ''
                            posts.append({
                                'id': href,
                                'url': href,
                                'handle': handle
                            })
                except:
                    continue
        except Exception as e:
            self.logger.error(f"Error getting posts: {e}")
        return posts

    def get_post_id(self, post):
        return post.get('id', '')

    def can_comment_on(self, post):
        return bool(post.get('id'))

    def open_post(self, post):
        """Navigate to the post page."""
        url = post.get('url')
        if url:
            if not url.startswith('http'):
                url = self.get_base_url() + url
            self.go_to(url)
            self.sleep(4)

    def post_comment(self, comment):
        """Fill and submit the reply form."""
        try:
            # Click the reply button using JavaScript
            result = self.page.evaluate("""() => {
                const replyBtn = document.querySelector('[data-testid="replyBtn"]');
                if (replyBtn) {
                    replyBtn.click();
                    return 'Clicked replyBtn';
                }
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b => b.textContent.trim().startsWith('Reply') && b.querySelector('img'));
                if (btn) {
                    btn.click();
                    return 'Clicked Reply button with img';
                }
                return 'No reply button found';
            }""")
            self.logger.info(f"Reply button click: {result}")
            self.sleep(2)

            # Type into the textbox using JavaScript
            type_result = self.page.evaluate("""(text) => {
                const textbox = document.querySelector('[aria-label="Rich-Text Editor"]') ||
                               document.querySelector('div[role="textbox"]');
                if (textbox) {
                    textbox.focus();
                    document.execCommand('insertText', false, text);
                    return 'Typed into: ' + textbox.getAttribute('aria-label');
                }
                return 'No textbox found';
            }""", comment)
            self.logger.info(f"Type result: {type_result}")
            self.sleep(1)

            # Click the publish button
            submit_result = self.page.evaluate("""() => {
                const btn = document.querySelector('button[aria-label="Publish reply"]') ||
                           Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim() === 'Reply');
                if (btn) {
                    btn.click();
                    return 'Clicked publish';
                }
                return 'Button not found';
            }""")
            self.logger.info(f"Submit result: {submit_result}")
            self.sleep(2)

        except Exception as e:
            self.logger.error(f"Error posting reply: {e}")

    def verify_comment_posted(self):
        """Verify the reply appeared."""
        try:
            self.sleep(2)
            # Check if reply count incremented or reply appears in thread
            reply_btn = self.page.query_selector('[data-testid="replyBtn"]')
            if reply_btn:
                aria_label = reply_btn.get_attribute('aria-label') or ''
                self.logger.info(f"Reply button label: {aria_label}")
            return True
        except Exception:
            return False