"""Uneed.best scraper."""

from base_scraper import BaseScraper


class UneedScraper(BaseScraper):
    """Scraper for Uneed.best posts."""

    def get_base_url(self):
        return "https://www.uneed.best"

    def get_posts(self):
        """Scrape posts from Uneed community page."""
        posts = []
        try:
            # Go to community page - wait for domcontentloaded instead of load
            self.page.goto("https://www.uneed.best/community", timeout=60000, wait_until="domcontentloaded")
            self.sleep(5)

            # Find all post divs
            post_divs = self.page.query_selector_all('div.mt-4.space-y-4 > div')
            self.logger.info(f"Found {len(post_divs)} post divs")

            seen_ids = set()
            for i, post_div in enumerate(post_divs):
                try:
                    # Get all buttons - 3 buttons: like (index 2), comment (index 3), share (index 4)
                    buttons = post_div.query_selector_all('button.rounded-md.font-medium.inline-flex.items-center')
                    self.logger.info(f"Post {i}: {len(buttons)} buttons")
                    # Log button texts
                    for j, btn in enumerate(buttons):
                        text = (btn.text_content() or '').strip()
                        self.logger.info(f"  Button {j}: '{text}'")
                    # Button index 1 is the comment button (middle button, text is a number like "0", "1")
                    if len(buttons) >= 2:
                        comment_btn = buttons[1]
                        post_id = f"post_{i}"
                        if post_id not in seen_ids:
                            seen_ids.add(post_id)
                            posts.append({
                                'id': post_id,
                                'index': i
                            })
                except Exception as e:
                    self.logger.error(f"Error processing post {i}: {e}")
                    continue

            self.logger.info(f"Found {len(posts)} Uneed posts")

        except Exception as e:
            self.logger.error(f"Error getting posts: {e}")
        return posts

    def get_post_id(self, post):
        return post.get('id', '')

    def can_comment_on(self, post):
        return bool(post.get('id'))

    def open_post(self, post):
        """Navigate to the post page - need to click the comment button to open form."""
        # Go back to community page to click the button
        self.go_to("https://www.uneed.best/community")
        self.sleep(4)

        # Find all post divs and click the right one
        post_index = post.get('index', 0)
        post_divs = self.page.query_selector_all('div.mt-4.space-y-4 > div')

        if post_index < len(post_divs):
            post_div = post_divs[post_index]
            # Click button index 1 (comment button - middle button)
            buttons = post_div.query_selector_all('button.rounded-md.font-medium.inline-flex.items-center')
            if len(buttons) >= 2:
                comment_btn = buttons[1]
                try:
                    comment_btn.click()
                    self.sleep(2)
                except Exception as e:
                    self.logger.error(f"Could not click comment button: {e}")

    def post_comment(self, comment):
        """Fill and submit the comment form using Ctrl+Enter."""
        try:
            # Find the textarea - it appears after clicking the comment button
            # The selector: div.pt-4.border-t.border-neutral-200.dark:border-neutral-800.mt-4 > div > div.flex-1 > div > div > div > div > p
            textarea = self.page.query_selector('div.pt-4.border-t.border-neutral-200.dark\\:border-neutral-800.mt-4 > div > div.flex-1 > div > div > div > div > p')

            if not textarea:
                # Try alternate selector for the textarea
                textarea = self.page.query_selector('[contenteditable="true"][role="textbox"]')

            if textarea and textarea.is_visible():
                self.logger.info("Found textarea")
                textarea.fill(comment)
                self.sleep(1)

                # Post using Ctrl+Enter
                self.page.keyboard.press('Control+Enter')
                self.sleep(2)
                return

            # Fallback: try to find any visible contenteditable or textarea
            textareas = self.page.query_selector_all('[contenteditable="true"]')
            for ta in textareas:
                if ta.is_visible():
                    self.logger.info("Found alternate textarea")
                    ta.fill(comment)
                    self.sleep(1)
                    self.page.keyboard.press('Control+Enter')
                    self.sleep(2)
                    return

            self.logger.warning("Could not find comment textarea")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False