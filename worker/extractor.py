"""
Safe Web Extractor Module
Extracts product pricing, availability, and metadata using schema.org JSON-LD, OpenGraph,
and standard DOM structures. Integrates SSRF protection and robots.txt compliance.
"""

import re
import json
import logging
from decimal import Decimal
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
import httpx
from app.core.security import validate_url_ssrf_safe, is_scraping_permitted_by_robots
from worker.config import worker_settings

logger = logging.getLogger(__name__)

# Price extraction regular expressions
PRICE_REGEX = re.compile(r"[\$€£₹]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{2})|[0-9]+(?:\.[0-9]{2}))")


def parse_price_str(raw: str) -> Optional[Decimal]:
    if not raw:
        return None
    cleaned = raw.replace(",", "").strip()
    match = PRICE_REGEX.search(cleaned)
    if match:
        try:
            return Decimal(match.group(1))
        except Exception:
            return None
    return None


def extract_from_json_ld(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extracts schema.org/Product structured data if present."""
    data = {}
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            content = json.loads(script.string or "{}")
            if isinstance(content, list):
                items = content
            elif isinstance(content, dict) and "@graph" in content:
                items = content["@graph"]
            else:
                items = [content]

            for item in items:
                if not isinstance(item, dict):
                    continue
                type_val = item.get("@type", "")
                if type_val == "Product" or "Product" in type_val:
                    data["title"] = item.get("name")
                    data["description"] = item.get("description")
                    data["image_url"] = item.get("image")
                    if isinstance(data["image_url"], list) and data["image_url"]:
                        data["image_url"] = data["image_url"][0]

                    offers = item.get("offers")
                    if isinstance(offers, dict):
                        data["price"] = parse_price_str(str(offers.get("price", "")))
                        data["currency"] = offers.get("priceCurrency", "USD")
                        availability = offers.get("availability", "")
                        data["in_stock"] = "InStock" in availability
                    elif isinstance(offers, list) and offers:
                        first_offer = offers[0]
                        data["price"] = parse_price_str(str(first_offer.get("price", "")))
                        data["currency"] = first_offer.get("priceCurrency", "USD")
                    return data
        except Exception as e:
            logger.debug("Failed parsing JSON-LD script: %s", e)
    return data


def extract_from_meta_tags(soup: BeautifulSoup) -> Dict[str, Any]:
    """Extracts OpenGraph, Twitter, and ecommerce standard meta tags."""
    data = {}
    
    # Title
    og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "twitter:title"})
    if og_title and og_title.get("content"):
        data["title"] = og_title["content"].strip()
    elif soup.title and soup.title.string:
        data["title"] = soup.title.string.strip()

    # Image
    og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "twitter:image"})
    if og_img and og_img.get("content"):
        data["image_url"] = og_img["content"].strip()

    # Price from meta
    price_meta = (
        soup.find("meta", property="product:price:amount")
        or soup.find("meta", property="og:price:amount")
        or soup.find("meta", attrs={"itemprop": "price"})
    )
    if price_meta and price_meta.get("content"):
        data["price"] = parse_price_str(price_meta["content"])

    curr_meta = soup.find("meta", property="product:price:currency") or soup.find("meta", property="og:price:currency")
    if curr_meta and curr_meta.get("content"):
        data["currency"] = curr_meta["content"].strip().upper()

    return data


async def fetch_and_extract_product(url: str) -> Dict[str, Any]:
    """
    Safely fetches a product page, verifies SSRF safety, checks robots.txt,
    and extracts pricing and metadata.
    """
    # 1. SSRF Safety Check
    is_safe, reason, canonical = validate_url_ssrf_safe(url)
    if not is_safe or not canonical:
        raise ValueError(f"SSRF Protection triggered: {reason}")

    # 2. Robots.txt Compliance Check
    permitted, robot_reason = await is_scraping_permitted_by_robots(canonical, worker_settings.USER_AGENT)
    if not permitted:
        raise PermissionError(f"Scraping disallowed by website policy: {robot_reason}")

    headers = {
        "User-Agent": worker_settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }

    async with httpx.AsyncClient(
        timeout=worker_settings.FETCH_TIMEOUT_SECONDS,
        follow_redirects=True,
        max_redirects=3,
    ) as client:
        response = await client.get(canonical, headers=headers)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    # Priority 1: JSON-LD structured data
    result = extract_from_json_ld(soup)

    # Priority 2: Meta tags fallback
    meta_info = extract_from_meta_tags(soup)
    for k, v in meta_info.items():
        if v and not result.get(k):
            result[k] = v

    # Fallback title if none found
    if not result.get("title") and soup.title:
        result["title"] = soup.title.string.strip()

    # Defaults
    if "currency" not in result or not result["currency"]:
        result["currency"] = "USD"
    if "in_stock" not in result:
        result["in_stock"] = True

    return result
