"""
Playwright Automation Module
Permitted browser automation for client-rendered Single Page Applications (SPAs).
Enforces SSRF prevention, robots.txt check, and sandboxed headless execution.
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from app.core.security import validate_url_ssrf_safe, is_scraping_permitted_by_robots
from worker.config import worker_settings
from worker.extractor import extract_from_json_ld, extract_from_meta_tags, parse_price_str

logger = logging.getLogger(__name__)


async def scrape_with_playwright(url: str) -> Dict[str, Any]:
    """
    Renders product page using headless Chromium to capture dynamic JavaScript prices.
    Strictly verifies SSRF and robots.txt prior to browser navigation.
    """
    # 1. SSRF Safety Check
    is_safe, reason, canonical = validate_url_ssrf_safe(url)
    if not is_safe or not canonical:
        raise ValueError(f"SSRF Protection triggered: {reason}")

    # 2. Robots.txt Compliance Check
    permitted, robot_reason = await is_scraping_permitted_by_robots(canonical, worker_settings.USER_AGENT)
    if not permitted:
        raise PermissionError(f"Scraping disallowed by website policy: {robot_reason}")

    extracted_data: Dict[str, Any] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=worker_settings.HEADLESS_BROWSER,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
            ],
        )
        try:
            context = await browser.new_context(
                user_agent=worker_settings.USER_AGENT,
                viewport={"width": 1280, "height": 800},
                java_script_enabled=True,
            )
            page = await context.new_page()

            # Set timeout
            page.set_default_timeout(worker_settings.FETCH_TIMEOUT_SECONDS * 1000)

            # Navigate
            response = await page.goto(canonical, wait_until="domcontentloaded")
            if not response or response.status >= 400:
                raise RuntimeError(f"Browser navigation returned HTTP status {response.status if response else 'Unknown'}")

            # Wait briefly for client-side rendering
            await page.wait_for_timeout(1500)

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "lxml")

            # Extract structured data
            extracted_data = extract_from_json_ld(soup)
            meta_data = extract_from_meta_tags(soup)
            for k, v in meta_data.items():
                if v and not extracted_data.get(k):
                    extracted_data[k] = v

            # If title is still missing, grab page title
            if not extracted_data.get("title"):
                extracted_data["title"] = await page.title()

            # Fallback DOM price heuristics for common ecommerce structures
            if not extracted_data.get("price"):
                for selector in [
                    "[itemprop='price']",
                    ".price",
                    ".product-price",
                    "#priceblock_ourprice",
                    "#priceblock_dealprice",
                    ".a-price-whole",
                ]:
                    elem = await page.query_selector(selector)
                    if elem:
                        text_val = await elem.inner_text()
                        price_val = parse_price_str(text_val)
                        if price_val:
                            extracted_data["price"] = price_val
                            break

            await context.close()
        finally:
            await browser.close()

    if "currency" not in extracted_data:
        extracted_data["currency"] = "USD"
    if "in_stock" not in extracted_data:
        extracted_data["in_stock"] = True

    return extracted_data
