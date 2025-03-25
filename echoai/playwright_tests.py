#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: tt.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-03-24 16:15:16
# Modified: 2025-03-24 16:17:29

import random
import time
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

def get_website_data_dynamic(url: str, headless: bool = True, viewport_height: int = 20000) -> dict:
    """
    Extract all viewable text from a webpage given a URL, including dynamically loaded content,
    with an adjustable viewport height to optimize loading speed.

    Args:
        url (str): The URL of the webpage to extract text from.
        headless (bool, optional): Whether to run the browser in headless mode (default: True).
        viewport_height (int, optional): Height of the browser viewport in pixels (default: 10000).

    Returns:
        dict: A dictionary containing:
            - status (str): 'success' or 'error'
            - text (str, optional): The extracted and cleaned text if successful
            - url (str): The original URL
            - error (str, optional): Error message if the operation failed
    """
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/124.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/124.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15',
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            # Set a wide viewport with an abnormally large height
            page = browser.new_page(
                user_agent=random.choice(USER_AGENTS),
                viewport={"width": 1920, "height": viewport_height}
            )

            # Navigate with lenient wait strategy
            page.goto(url, wait_until="domcontentloaded", timeout=60000)

            if not headless:
                print("Page loaded, checking content in 2 seconds...")
                time.sleep(2)

            # Scroll only if necessary
            previous_height = page.evaluate("document.body.scrollHeight")
            max_scrolls = 10  # Reduced since large viewport loads more initially
            for i in range(max_scrolls):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                if not headless:
                    print(f"Scroll {i + 1}/{max_scrolls}")
                time.sleep(3)  # Reduced wait time since most content should already be loaded
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    if not headless:
                        print("No new content, stopping scroll.")
                    break
                previous_height = new_height
            else:
                if not headless:
                    print("Max scrolls reached, proceeding with what’s loaded.")
                # Don’t fail, just proceed with what’s available

            # Extract and clean the text
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            text = soup.get_text()
            cleaned_text = " ".join(text.split())

            if not headless:
                browser.close()

            return {
                "status": "success",
                "text": cleaned_text,
                "url": url
            }

    except TimeoutError as e:
        return {
            "status": "error",
            "error": f"Timeout while loading page: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Error: {str(e)}",
            "url": url
        }

if __name__ == "__main__":
    result = get_website_data_dynamic("https://cnn.com", headless=True)
    if result["status"] == "success":
        print("Extracted text:", result["text"])
    else:
        print("Error:", result["error"])
