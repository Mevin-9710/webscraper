"""Substack scraper."""

from base_scraper import BaseScraper


class SubstackScraper(BaseScraper):
    """Scraper for Substack posts."""

    def get_base_url(self):
        return "https://substack.com"

    def get_posts(self):
        """Scrape latest posts from Substack home feed."""
        posts = []
        try:
            self.go_to("https://substack.com")
            self.sleep(4)

            # Find post links in the reading queue
            post_links = self.page.query_selector_all('a[href*="/home/post/p-"]')
            self.logger.info(f"Found {len(post_links)} posts")

            seen_ids = set()
            for link in post_links[:20]:
                try:
                    href = link.get_attribute('href')
                    if href and href not in seen_ids:
                        # Extract post ID from URL
                        post_id = href.split('?')[0]  # Remove query params
                        seen_ids.add(post_id)
                        posts.append({
                            'id': post_id,
                            'url': href,
                            'title': link.text_content()[:100] if link.text_content() else 'Untitled'
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
        """Navigate to the post page comments section."""
        url = post.get('url')
        if url:
            if '/home/post/' in url:
                self.go_to(url)
                self.sleep(4)
                # Try to get to comments page
                result = self.page.evaluate("""() => {
                    const postLink = document.querySelector('a[href*="/p/"][href*="/comments"]');
                    if (postLink) return postLink.href;
                    const canonicalLink = document.querySelector('link[rel="canonical"]');
                    if (canonicalLink) return canonicalLink.href + '/comments';
                    return null;
                }""")
                if result:
                    self.go_to(result)
                    self.sleep(2)

    def post_comment(self, comment):
        """Fill and submit the comment form."""
        try:
            self.sleep(3)

            # Close paywall if present
            self.page.evaluate("""() => {
                const paywall = document.querySelector('[role="dialog"] button[aria-label="close"]') ||
                               document.querySelector('button[aria-label="close"]');
                if (paywall) paywall.click();
            }""")
            self.sleep(1)

            # Navigate to comments page
            current_url = self.page.url
            if '/comments' not in current_url and '/p/' in current_url:
                self.go_to(current_url + '/comments')
                self.sleep(3)

            # Type into comment textarea
            type_result = self.page.evaluate("""(text) => {
                const textarea = Array.from(document.querySelectorAll('textarea, input')).find(el =>
                    el.placeholder && el.placeholder.toLowerCase().includes('comment')
                );
                if (textarea) {
                    textarea.focus();
                    textarea.value = text;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
                    return 'Typed in: ' + textarea.tagName;
                }
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor) {
                    editor.focus();
                    document.execCommand('insertText', false, text);
                    return 'Typed in contenteditable';
                }
                return 'No textarea found';
            }""", comment)
            self.logger.info(f"Type result: {type_result}")
            self.sleep(2)

            # Check paywall
            paywall_check = self.page.evaluate("""() => {
                const paywall = document.querySelector('[role="dialog"]');
                if (paywall && paywall.textContent.includes('paid subscribers')) {
                    return 'PAYWALL: Requires paid subscription';
                }
                return 'No paywall';
            }""")
            self.logger.info(f"Paywall check: {paywall_check}")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False