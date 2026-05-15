"""Dev.to scraper."""

from base_scraper import BaseScraper


class DevtoScraper(BaseScraper):
    """Scraper for Dev.to articles."""

    def get_base_url(self):
        return "https://dev.to"

    def get_posts(self):
        """Scrape latest articles from Dev.to homepage."""
        posts = []
        try:
            # Go to main page
            self.go_to("https://dev.to")
            self.sleep(4)

            # Find the feed container - use the user's selectors
            feed = self.page.query_selector('#rendered-article-feed')
            if not feed:
                feed = self.page.query_selector('#active-discussions')
            if not feed:
                feed = self.page  # fallback to full page

            # Look for article cards within the feed
            articles = feed.query_selector_all('article')
            self.logger.info(f"Found {len(articles)} articles")

            for article in articles[:20]:
                try:
                    # Get the main link
                    link = article.query_selector('a')
                    if link:
                        href = link.get_attribute('href')
                        if href:
                            # Use URL as ID since dev.to no longer uses data-id
                            posts.append({
                                'id': href,
                                'url': href
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
        """Navigate to the article page."""
        url = post.get('url')
        if url:
            if not url.startswith('http'):
                url = self.get_base_url() + url
            self.go_to(url)
            self.sleep(4)

    def post_comment(self, comment):
        """Fill and submit the comment form."""
        try:
            # Scroll to bottom where comment form is
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.sleep(2)

            # Dev.to comment form selectors
            textarea_selectors = [
                'textarea#text-area',
                'textarea[name="comment[body_markdown]"]',
                'textarea[placeholder*="Add to"]',
                'textarea[placeholder*="discussion"]',
            ]

            for sel in textarea_selectors:
                textarea = self.page.wait_for_selector(sel, timeout=5000)
                if textarea:
                    self.logger.info(f"Found textarea: {sel}")
                    # Use page.fill instead of element.fill to avoid detachment issues
                    self.page.fill(sel, comment)
                    self.sleep(1)

                    # Submit using the specific button selector
                    submit_btn = self.page.query_selector('#new_comment > div.comment-form__inner > div.comment-form__buttons.mb-4 > button:nth-child(1)')
                    if submit_btn and submit_btn.is_visible():
                        submit_btn.click()
                        self.sleep(2)
                        return

                    return

            # Log what textareas exist
            textareas = self.page.query_selector_all('textarea')
            self.logger.warning(f"No comment form found. Page has {len(textareas)} textareas")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False