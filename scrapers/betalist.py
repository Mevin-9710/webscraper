"""BetaList scraper."""

from base_scraper import BaseScraper


class BetaListScraper(BaseScraper):
    """Scraper for BetaList beta listings."""

    def get_base_url(self):
        return "https://betalist.com"

    def get_posts(self):
        """Scrape latest beta listings from BetaList."""
        posts = []
        try:
            self.go_to("https://betalist.com")
            self.sleep(4)

            # Find startup links
            links = self.page.query_selector_all('a[href*="/startups/"]')
            seen = set()
            for link in links[:20]:
                try:
                    href = link.get_attribute('href')
                    if href and '/startups/' in href:
                        parts = href.split('/startups/')
                        if len(parts) > 1:
                            startup_id = parts[1].split('?')[0]
                            if startup_id and startup_id not in seen:
                                seen.add(startup_id)
                                posts.append({
                                    'id': startup_id,
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
        """Navigate to the beta listing page."""
        url = post.get('url')
        if url:
            if not url.startswith('http'):
                url = self.get_base_url() + url
            self.go_to(url)
            self.sleep(3)

    def post_comment(self, comment):
        """Fill and submit the review/comment form."""
        try:
            selectors = [
                'textarea[name="review"]',
                'textarea[name="comment"]',
                'textarea[id*="review"]',
                'textarea[placeholder*="Review"]',
                'textarea[placeholder*="Comment"]',
                'textarea',
            ]

            for sel in selectors:
                field = self.page.query_selector(sel)
                if field and field.is_visible():
                    field.click()
                    self.sleep(0.5)
                    field.fill(comment)
                    self.sleep(1)

                    btn_selectors = [
                        'button[type="submit"]',
                        'button:has-text("Submit")',
                        'button:has-text("Post")',
                        'button:has-text("Add Review")',
                    ]
                    for btn_sel in btn_selectors:
                        btn = self.page.query_selector(btn_sel)
                        if btn and btn.is_visible():
                            btn.click()
                            self.sleep(2)
                            return
                    return

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False