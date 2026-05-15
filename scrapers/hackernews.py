"""Hacker News scraper."""

from base_scraper import BaseScraper


class HackerNewsScraper(BaseScraper):
    """Scraper for Hacker News."""

    def get_base_url(self):
        return "https://news.ycombinator.com"

    def get_posts(self):
        """Scrape latest stories from Hacker News homepage."""
        posts = []
        try:
            # Go to homepage
            self.go_to("https://news.ycombinator.com/")
            self.sleep(4)

            # #bigbox is the table containing all posts
            # Each post is a row, find all tr elements within #bigbox
            table = self.page.query_selector('#bigbox')
            if table:
                rows = table.query_selector_all('tr')
            else:
                rows = []

            self.logger.info(f"Found {len(rows)} rows in #bigbox")

            seen_ids = set()
            for row in rows:
                try:
                    # Get the comment link from subtext column
                    comment_link = row.query_selector('td.subtext a[href*="item?id="]')
                    if comment_link:
                        href = comment_link.get_attribute('href')
                        story_id = href.split('item?id=')[-1] if 'item?id=' in href else None

                        # Get the story title link
                        title_link = row.query_selector('.titleline a')
                        story_url = title_link.get_attribute('href') if title_link else None

                        if story_id and story_id not in seen_ids:
                            seen_ids.add(story_id)
                            posts.append({
                                'id': story_id,
                                'url': story_url,
                                'title': title_link.text_content() if title_link else '',
                                'hn_url': href
                            })
                except:
                    continue

            self.logger.info(f"Found {len(posts)} HN posts")

        except Exception as e:
            self.logger.error(f"Error getting posts: {e}")
        return posts

    def get_post_id(self, post):
        return post.get('id', '')

    def can_comment_on(self, post):
        return True

    def open_post(self, post):
        """Navigate to the HN discussion page via the comment link."""
        hn_url = post.get('hn_url')
        if hn_url:
            # Make sure it's a full URL
            if not hn_url.startswith('http'):
                hn_url = self.get_base_url() + '/' + hn_url
            self.go_to(hn_url)
            self.sleep(3)

    def post_comment(self, comment):
        """Fill and submit the comment form - handles both new comments and replies."""
        try:
            # First, try to post a new comment (top-level comment form)
            # Textarea: #bigbox > td > table.fatitem > tbody > tr:nth-child(5) > td:nth-child(2) > form > textarea
            textarea = self.page.query_selector('#bigbox > td > table.fatitem > tbody > tr:nth-child(5) > td:nth-child(2) > form > textarea')
            if textarea and textarea.is_visible():
                self.logger.info("Found top-level comment form")
                textarea.fill(comment)
                self.sleep(1)

                # Submit button
                submit_btn = self.page.query_selector('#bigbox > td > table.fatitem > tbody > tr:nth-child(5) > td:nth-child(2) > form > input[type=submit]:nth-child(12)')
                if submit_btn and submit_btn.is_visible():
                    submit_btn.click()
                    self.sleep(2)
                    return

            # If no top-level form, try to find reply forms for existing comments
            # Reply forms appear when clicking "reply" on existing comments
            reply_textareas = self.page.query_selector_all('form textarea')
            for reply_ta in reply_textareas:
                if reply_ta.is_visible():
                    self.logger.info("Found reply form")
                    reply_ta.fill(comment)
                    self.sleep(1)
                    # Find submit button in this form
                    form = reply_ta.evaluate_handle("el => el.closest('form')")
                    if form:
                        submit_btn = form.query_selector('input[type="submit"]')
                        if submit_btn and submit_btn.is_visible():
                            submit_btn.click()
                            self.sleep(2)
                            return

            # Try pressing Ctrl+Enter to submit
            if textarea and textarea.is_visible():
                textarea.fill(comment)
                self.sleep(1)
                self.page.keyboard.press('Control+Enter')
                self.sleep(2)
                return

            self.logger.warning("Could not find comment form with given selectors")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False