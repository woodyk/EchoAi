#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# File: WebFormAnalyzer.py
# Author: Wadih Khairallah
# Description: CLI Tool for analyzing web forms and inputs on a given URL
# Created: 2024-12-04
# Modified: 2025-06-18

import logging
import sys
import json
import argparse
from urllib.parse import urljoin
from selenium import webdriver
from selenium.common.exceptions import (
    WebDriverException,
    TimeoutException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to initialize WebDriver
def init_driver(headless=True, browser='firefox', page_load_timeout=30):
    try:
        if browser.lower() == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Firefox(options=options)
        elif browser.lower() == 'chrome':
            options = ChromeOptions()
            if headless:
                options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
        else:
            raise ValueError("Browser must be 'firefox' or 'chrome'")
        driver.set_page_load_timeout(page_load_timeout)
        return driver
    except WebDriverException as e:
        logging.error(f"Error initializing WebDriver: {e}")
        sys.exit(1)

# Function to analyze site forms
def analyze_site_features(url, headless=True, browser='firefox', wait_time=10):
    driver = init_driver(headless=headless, browser=browser)
    try:
        logging.info(f"Accessing URL: {url}")
        driver.get(url)
        WebDriverWait(driver, wait_time).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'form')))
        
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        forms = soup.find_all('form')
        features = []
        for form in forms:
            action = form.get('action')
            method = form.get('method', 'GET').upper()
            inputs = []
            for input_tag in form.find_all(['input', 'textarea', 'select']):
                input_type = input_tag.get('type', 'text')
                input_name = input_tag.get('name')
                # For select elements, get options
                if input_tag.name == 'select':
                    options = [option.get('value') or option.text for option in input_tag.find_all('option')]
                    inputs.append({'type': 'select', 'name': input_name, 'options': options})
                else:
                    inputs.append({'type': input_type, 'name': input_name})
            form_details = {
                'action': urljoin(url, action) if action else url,
                'method': method,
                'inputs': inputs
            }
            features.append(form_details)
        return features
    except TimeoutException:
        logging.error(f"Timeout while loading {url}")
    except Exception as e:
        logging.error(f"Error analyzing site features: {e}")
    finally:
        driver.quit()
    return []

def main():
    parser = argparse.ArgumentParser(description='Analyze web forms and inputs on a given URL.')
    parser.add_argument('url', help='URL of the website to analyze.')
    parser.add_argument('--headless', action='store_true', default=True, help='Run browser in headless mode (default: True).')
    parser.add_argument('--browser', choices=['firefox', 'chrome'], default='firefox', help='Browser to use (default: firefox).')
    parser.add_argument('--output-format', choices=['json', 'plain'], default='plain', help='Output format (default: plain).')
    parser.add_argument('--wait-time', type=int, default=10, help='Element wait time in seconds (default: 10).')

    args = parser.parse_args()

    features = analyze_site_features(args.url, headless=args.headless, browser=args.browser, wait_time=args.wait_time)
    
    if args.output_format == 'json':
        print(json.dumps(features, indent=2))
    else:
        print(f"Site Features of {args.url}:")
        for form in features:
            print(f"Form action: {form['action']}")
            print(f"Method: {form['method']}")
            print("Inputs:")
            for input_field in form['inputs']:
                print(f" - Name: {input_field.get('name')}, Type: {input_field.get('type')}")
                if input_field.get('type') == 'select':
                    print(f" Options: {input_field.get('options')}")
            print("-" * 40)

if __name__ == "__main__":
    main()
