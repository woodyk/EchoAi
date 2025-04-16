#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: search_duckduckgo.py
# Author: Wadih Khairallah
# Description: 
# Created: 2025-04-04 23:57:22
# Modified: 2025-04-08 15:51:02

import os
import re
import json
import asyncio
import urllib.parse as urlparse
from typing import Dict, Any, List

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from rich.console import Console

console = Console()
print = console.print

def search_duckduckgo(query: str, num_results: int = 5) -> Dict[str, Any]:
    """
    Search DuckDuckGo using Selenium in parallel (1 browser per URL).
    """

    def clean_text(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()

    def extract_text_with_selenium_new_driver(url: str) -> str:
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1280,800")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
            )

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            driver.get(url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
            return clean_text(soup.get_text())
        except Exception as e:
            return f"[Selenium Error] {url}: {str(e)}"
        finally:
            try:
                driver.quit()
            except:
                pass

    def get_duckduckgo_result_urls(query: str, num_results: int) -> List[str]:
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1280,800")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
        )

        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

        try:
            search_url = f"https://duckduckgo.com/?q={urlparse.quote_plus(query)}&ia=web"
            driver.get(search_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']"))
            )

            elements = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
            urls = [e.get_attribute("href") for e in elements[:num_results]]
            return urls
        except Exception as e:
            print(f"[Error] Failed to get DuckDuckGo results: {e}")
            return []
        finally:
            driver.quit()

    async def run_parallel_extractions(urls: List[str]):
        tasks = []
        for url in urls:
            print(f"  → [blue]Queued:[/blue] {url}")
            tasks.append(asyncio.to_thread(extract_text_with_selenium_new_driver, url))
        return await asyncio.gather(*tasks, return_exceptions=True)

    # Start the process
    console.print(f"[cyan]Searching DuckDuckGo:[/cyan] {query}")

    try:
        urls = get_duckduckgo_result_urls(query, num_results)
        if not urls:
            return {
                "status": "error",
                "error": f"No results returned for: {query}",
                "urls": [],
                "query": query
            }

        extracted_texts = asyncio.run(run_parallel_extractions(urls))

        return {
            "status": "success",
            "text": " ".join([t if isinstance(t, str) else f"[Error] {t}" for t in extracted_texts]),
            "urls": urls,
            "error": None,
            "query": query
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Selenium DuckDuckGo search failed: {str(e)}",
            "query": query
        }

# Run directly
if __name__ == "__main__":
    import time
    search_query = input("Enter DuckDuckGo search query: ").strip()
    start = time.time()
    result = search_duckduckgo(search_query)
    end = time.time()
    print(json.dumps(result, indent=2))
    print(f"\n[bold green]Time taken:[/bold green] {end - start:.2f} seconds")

