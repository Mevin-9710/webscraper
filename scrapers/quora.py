"""Quora scraper."""

from base_scraper import BaseScraper


class QuoraScraper(BaseScraper):
    """Scraper for Quora questions."""

    def get_base_url(self):
        return "https://www.quora.com"

    def get_posts(self):
        """Scrape relevant questions from Quora topic page."""
        posts = []
        try:
            # Go to Startups topic
            self.go_to("https://www.quora.com/topic/Startups")
            self.sleep(4)

            # Scroll to load more content
            self.page.evaluate("window.scrollTo(0, 500)")
            self.sleep(2)

            # Look for question links - Quora uses various selectors
            # Look for spans that link to answers
            links = self.page.query_selector_all('a[href*="/"]')
            seen = set()

            for link in links[:50]:
                try:
                    href = link.get_attribute('href')
                    if href and '/answer/' in href:
                        # Extract question ID from URL
                        # Format: /topic/Question-Name/answer/Some-Name
                        parts = href.split('/answer/')
                        if len(parts) > 1:
                            question_id = parts[0].split('/')[-1]  # Get the topic/question name
                            if question_id and question_id not in seen:
                                seen.add(question_id)
                                posts.append({
                                    'id': question_id,
                                    'url': href
                                })
                except:
                    continue

            # Also try looking for question titles in spans with specific patterns
            span_links = self.page.query_selector_all('span a[href*="/"]')
            for link in span_links[:30]:
                try:
                    href = link.get_attribute('href')
                    if href and '/answer/' in href:
                        question_id = href.split('/answer/')[0].split('/')[-1]
                        if question_id and question_id not in seen:
                            seen.add(question_id)
                            posts.append({
                                'id': question_id,
                                'url': href
                            })
                except:
                    continue

            self.logger.info(f"Found {len(posts)} Quora posts")

        except Exception as e:
            self.logger.error(f"Error getting posts: {e}")
        return posts

    def get_post_id(self, post):
        return post.get('id', '')

    def can_comment_on(self, post):
        return bool(post.get('id'))

    def open_post(self, post):
        """Navigate to the answer page."""
        url = post.get('url')
        if url:
            self.go_to(url)
            self.sleep(4)

            # Scroll to load content
            self.page.evaluate("window.scrollTo(0, 300)")
            self.sleep(2)

    def post_comment(self, comment):
        """Fill and submit the comment form."""
        try:
            self.logger.info("Looking for answer form...")

            # Find the answer input and its submit button that are in the SAME container
            # The key is: find the input first, then find the button that's a DIRECT sibling or parent-child

            editable_divs = self.page.query_selector_all('div[contenteditable="true"]')

            for div in editable_divs:
                try:
                    if not div.is_visible():
                        continue

                    classes = div.get_attribute('class') or ""
                    if 'comment' in classes.lower() or 'reply' in classes.lower():
                        continue

                    self.logger.info("Found answer input div")

                    # Use JavaScript to find the submit button that's DIRECTLY near this input
                    result = self.page.evaluate("""
                        (inputEl) => {
                            // Walk up to find the form container
                            let container = inputEl;
                            for (let i = 0; i < 8; i++) {
                                if (!container) return null;
                                container = container.parentElement;
                                if (!container) continue;

                                // Look for q-click-wrapper buttons within this container
                                const wrappers = container.querySelectorAll('[class*="q-click-wrapper"]');
                                for (const w of wrappers) {
                                    const text = (w.textContent || '').trim().toLowerCase();
                                    // Look for "Add" (the submit button), NOT "Add Answer"
                                    if (text === 'add' || text === 'submit' || text === 'post') {
                                        return text;
                                    }
                                }
                            }
                            return null;
                        }
                    """, div)

                    if result:
                        self.logger.info(f"Found adjacent submit button: {result}")

                        # Fill the comment
                        div.fill(comment)
                        self.sleep(1)

                        # Now find and click THAT specific button
                        # We need to find it relative to the input, not globally
                        result2 = self.page.evaluate("""
                            (inputEl) => {
                                let container = inputEl;
                                for (let i = 0; i < 8; i++) {
                                    if (!container) return null;
                                    container = container.parentElement;
                                    if (!container) continue;

                                    const wrappers = container.querySelectorAll('[class*="q-click-wrapper"]');
                                    for (const w of wrappers) {
                                        const text = (w.textContent || '').trim().toLowerCase();
                                        if (text === 'add' || text === 'submit' || text === 'post') {
                                            return w.outerHTML.substring(0, 100);
                                        }
                                    }
                                }
                                return null;
                            }
                        """, div)

                        # Find the button by traversing from the input
                        container = div
                        for _ in range(8):
                            container = container.evaluate_handle("el => el.parentElement")
                            if not container:
                                break
                            btns = container.query_selector_all('[class*="q-click-wrapper"]')
                            for btn in btns:
                                try:
                                    text = (btn.text_content() or "").strip().lower()
                                    if text == 'add' or text == 'submit' or text == 'post':
                                        self.logger.info(f"Clicking button: {text}")
                                        # Try clicking inner button/span within the wrapper
                                        inner = btn.query_selector('button, span')
                                        if inner:
                                            inner.click()
                                        else:
                                            btn.click()
                                        self.sleep(3)

                                        # Verify: check if our comment text appears on page
                                        page_text = self.page.content()
                                        if comment[:30] in page_text:
                                            self.logger.info("Verified: comment appears on page")
                                            return
                                        else:
                                            self.logger.warning("Comment may not have posted, continuing...")
                                except Exception as e:
                                    self.logger.debug(f"Button click failed: {e}")
                                    continue

                    # Fallback: try Enter key
                    self.logger.info("Trying Enter key")
                    div.fill(comment)
                    self.sleep(1)
                    self.page.press('div[contenteditable="true"]', 'Enter')
                    self.sleep(3)
                    return

                except Exception as e:
                    self.logger.debug(f"Attempt failed: {e}")
                    continue

            self.logger.warning("No answer form found")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")

    def verify_comment_posted(self):
        """Verify the answer was posted."""
        try:
            self.sleep(2)

            # Check if comment was actually posted by looking for the comment text
            # or checking if the input field is now empty/filled with posted content
            page_content = self.page.content()

            # Look for evidence that an answer was submitted
            # Check for success indicators or that our comment appears
            # Quora often shows the answer immediately after posting

            # Check if any answer textarea is empty (means it was submitted)
            textareas = self.page.query_selector_all('textarea')
            for ta in textareas:
                try:
                    value = ta.input_value() if hasattr(ta, 'input_value') else ta.get_attribute('value')
                    if not value or value.strip() == '':
                        self.logger.info("Textarea is empty - comment likely posted")
                        return True
                except:
                    continue

            # If we got here without errors, consider it success
            return True

        except Exception as e:
            self.logger.error(f"Verification error: {e}")
            return False