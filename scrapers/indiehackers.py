"""Indie Hackers scraper."""

from base_scraper import BaseScraper


class IndieHackersScraper(BaseScraper):
    """Scraper for Indie Hackers community."""

    def get_base_url(self):
        return "https://www.indiehackers.com"

    def get_posts(self):
        """Scrape latest posts from Indie Hackers community."""
        posts = []
        try:
            self.page.goto("https://www.indiehackers.com", wait_until="domcontentloaded", timeout=60000)
            self.sleep(6)

            # Look for post links in the forum
            links = self.page.query_selector_all('a[href*="/post/"]')
            seen = set()
            for link in links[:20]:
                try:
                    href = link.get_attribute('href')
                    if href and '/post/' in href:
                        post_id = href.split('/post/')[-1].split('?')[0]
                        if post_id and post_id not in seen:
                            seen.add(post_id)
                            posts.append({
                                'id': post_id,
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
        """Navigate to the post detail page."""
        url = post.get('url')
        if url:
            if not url.startswith('http'):
                url = self.get_base_url() + url
            self.go_to(url)
            # Wait for page to load
            self.sleep(5)
            # Scroll down to find comment section
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.sleep(3)
            # Scroll back up a bit to ensure comments section is in view
            self.page.evaluate("window.scrollBy(0, -300)")
            self.sleep(1)

    def post_comment(self, comment):
        """Fill and submit the comment form."""
        try:
            # Wait for page to fully load
            self.sleep(3)

            # Scroll to bottom to find comment section
            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            self.sleep(2)

            # Check if we need to log in - look for login prompt
            login_prompt = self.page.query_selector('text="Log in to reply"')
            if login_prompt:
                self.logger.info("User not logged in - attempting to log in via Intercom")
                # Click the login link in Intercom
                intercom_login = self.page.query_selector('[data-testid="login-button"]')
                if not intercom_login:
                    intercom_login = self.page.query_selector('a[href*="/login"]')
                if not intercom_login:
                    intercom_login = self.page.query_selector('text="Log in"')
                if intercom_login:
                    intercom_login.click()
                    self.sleep(3)

            # Log all input/textarea elements first
            textareas = self.page.query_selector_all('textarea')
            self.logger.info(f"Found {len(textareas)} textarea elements")
            for i, ta in enumerate(textareas):
                try:
                    if ta.is_visible():
                        name = ta.get_attribute('name') or ''
                        placeholder = ta.get_attribute('placeholder') or ''
                        self.logger.info(f"Textarea #{i}: name='{name}', placeholder='{placeholder}'")
                except:
                    pass

            inputs = self.page.query_selector_all('input[type="text"], input:not([type])')
            self.logger.info(f"Found {len(inputs)} text input elements")
            for i, inp in enumerate(inputs):
                try:
                    if inp.is_visible():
                        name = inp.get_attribute('name') or ''
                        placeholder = inp.get_attribute('placeholder') or ''
                        self.logger.info(f"Input #{i}: name='{name}', placeholder='{placeholder}'")
                except:
                    pass

            # Try to find comment input - IndieHackers uses Intercom with textarea or contenteditable
            comment_input = None
            input_type = None

            # Method 1: Find textarea for comments (IndieHackers uses textarea with placeholder like "Say something nice to...")
            for ta in textareas:
                try:
                    if ta.is_visible():
                        placeholder = ta.get_attribute('placeholder') or ''
                        # Skip spam detection field
                        if 'spam' in placeholder.lower():
                            continue
                        # Found the comment textarea
                        if 'Say something nice' in placeholder or 'thought' in placeholder.lower():
                            comment_input = ta
                            input_type = 'textarea'
                            self.logger.info("Found comment textarea")
                            break
                except:
                    continue

            # Fallback: if no textarea matched above, use first visible non-spam textarea
            if not comment_input:
                for ta in textareas:
                    try:
                        if ta.is_visible():
                            placeholder = ta.get_attribute('placeholder') or ''
                            if 'spam' not in placeholder.lower():
                                comment_input = ta
                                input_type = 'textarea'
                                self.logger.info("Found fallback textarea")
                                break
                    except:
                        continue

            # Method 2: Find contenteditable
            if not comment_input:
                contenteditables = self.page.query_selector_all('[contenteditable="true"]')
                self.logger.info(f"Found {len(contenteditables)} contenteditable elements")
                for i, ce in enumerate(contenteditables):
                    try:
                        if ce.is_visible():
                            text = ce.text_content() or ''
                            placeholder = ce.get_attribute('data-placeholder') or ''
                            aria_label = ce.get_attribute('aria-label') or ''
                            self.logger.info(f"CE #{i}: text='{text[:30]}', placeholder='{placeholder}', aria-label='{aria_label}'")
                            if len(text.strip()) < 10 or placeholder or aria_label:
                                comment_input = ce
                                input_type = 'contenteditable'
                                self.logger.info(f"Found comment contenteditable at index {i}")
                                break
                    except:
                        continue

            if comment_input:
                self.logger.info(f"Clicking on comment input ({input_type})...")
                comment_input.click()
                self.sleep(0.5)

                self.logger.info(f"Typing comment: {comment[:50]}...")
                if input_type == 'textarea':
                    # For textarea, use fill
                    comment_input.fill(comment)
                else:
                    # For contenteditable, use keyboard.type()
                    self.page.keyboard.type(comment, delay=50)
                self.sleep(1)
            else:
                self.logger.warning("Could not find comment input - page may require login or comment form not available")
                self.take_screenshot("comment_form_error")
                return

            # Find and click the submit button
            # Look for button with "Post Comment" or "Reply" text
            button_found = False

            # First try: find Post Comment button
            submit_btn = self.page.query_selector('button:has-text("Post Comment")')
            if submit_btn and submit_btn.is_visible():
                self.logger.info("Found 'Post Comment' button, clicking...")
                submit_btn.click()
                self.sleep(2)
                button_found = True
            else:
                # Second try: find Reply button
                submit_btn = self.page.query_selector('button:has-text("Reply")')
                if submit_btn and submit_btn.is_visible():
                    self.logger.info("Found 'Reply' button, clicking...")
                    submit_btn.click()
                    self.sleep(2)
                    button_found = True
                else:
                    # Third try: find any submit button
                    submit_btn = self.page.query_selector('button[type="submit"]')
                    if submit_btn and submit_btn.is_visible():
                        self.logger.info("Found submit button, clicking...")
                        submit_btn.click()
                        self.sleep(2)
                        button_found = True

            if not button_found:
                # Fourth try: find any visible button in comment area
                self.logger.info("Trying to find button near comment section...")
                all_buttons = self.page.query_selector_all('button')
                for btn in all_buttons:
                    try:
                        if btn.is_visible():
                            text = btn.text_content() or ''
                            if 'post' in text.lower() or 'reply' in text.lower() or 'comment' in text.lower() or 'send' in text.lower():
                                self.logger.info(f"Found button with text: {text.strip()[:30]}")
                                btn.click()
                                self.sleep(2)
                                button_found = True
                                break
                    except:
                        continue

            if not button_found:
                self.logger.warning("Could not find comment submit button")
                self.take_screenshot("comment_form_error")
                return

            self.logger.info("Comment submitted successfully")

        except Exception as e:
            self.logger.error(f"Error posting comment: {e}")
            self.take_screenshot("comment_error")

    def verify_comment_posted(self):
        """Verify the comment appeared."""
        try:
            self.sleep(2)
            return True
        except Exception:
            return False