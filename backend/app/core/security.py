"""
Security and SSRF Protection Module
Provides validation for user-submitted product URLs to prevent Server-Side Request Forgery (SSRF),
DNS rebinding, local network probing, and cloud metadata exfiltration.
Also provides robots.txt compliance checking to respect web access restrictions.
"""

import ipaddress
import socket
from urllib.parse import urlparse
from typing import Tuple, List, Optional
import urllib.robotparser
import httpx


# Forbidden hostnames (cloud metadata, local host aliases)
BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
    "169.254.169.254",
    "fd00::",
}

# Standard public web ports permitted
ALLOWED_PORTS = {80, 443}


def is_ip_address_safe(ip_str: str) -> Tuple[bool, str]:
    """
    Evaluates whether an IP address belongs to a public, routable network.
    Blocks private, loopback, link-local, multicast, cloud metadata, and reserved ranges.
    """
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False, f"Invalid IP address format: {ip_str}"

    # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped

    if ip.is_loopback:
        return False, f"Access to loopback address ({ip}) is prohibited"
    if ip.is_private:
        return False, f"Access to private internal network ({ip}) is prohibited"
    if ip.is_link_local:
        return False, f"Access to link-local address ({ip}) is prohibited"
    if ip.is_multicast:
        return False, f"Access to multicast address ({ip}) is prohibited"
    if ip.is_reserved:
        return False, f"Access to reserved address ({ip}) is prohibited"
    if ip.is_unspecified:
        return False, f"Access to unspecified address ({ip}) is prohibited"

    # Cloud metadata checks (AWS, Azure, GCP, DigitalOcean, OpenStack)
    cloud_metadata_nets = [
        ipaddress.ip_network("169.254.169.254/32"),
        ipaddress.ip_network("100.100.100.200/32"), # Alibaba cloud metadata
    ]
    if any(ip in net for net in cloud_metadata_nets):
        return False, f"Access to cloud metadata service ({ip}) is prohibited"

    return True, "Safe"


def validate_url_ssrf_safe(url: str, allowed_domains: Optional[List[str]] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Performs comprehensive SSRF validation on a user-submitted URL:
    1. Scheme check (strictly http or https).
    2. Hostname extraction & blacklist verification.
    3. Port validation (default 80/443 only).
    4. DNS resolution to all A/AAAA records.
    5. IP safety checks against private and internal subnets.

    Returns:
        (is_safe: bool, reason_message: str, canonical_url: Optional[str])
    """
    if not url or not isinstance(url, str):
        return False, "URL cannot be empty", None

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as exc:
        return False, f"Failed to parse URL: {str(exc)}", None

    # 1. Scheme Check
    if parsed.scheme.lower() not in ("http", "https"):
        return False, f"Unsupported URL scheme: {parsed.scheme}. Only http and https are allowed.", None

    # 2. Hostname Check
    hostname = parsed.hostname
    if not hostname:
        return False, "URL missing valid hostname", None

    hostname_lower = hostname.lower().strip(".")
    if hostname_lower in BLOCKED_HOSTNAMES:
        return False, f"Access to blocked hostname '{hostname}' is prohibited", None

    if hostname_lower.endswith(".internal") or hostname_lower.endswith(".local") or hostname_lower.endswith(".localhost"):
        return False, f"Access to internal domain '{hostname}' is prohibited", None

    # 3. Port Check
    port = parsed.port
    if port is not None and port not in ALLOWED_PORTS:
        return False, f"Port {port} is not permitted. Only ports 80 and 443 are allowed.", None

    # 4. Optional Domain Whitelist Filter
    if allowed_domains and len(allowed_domains) > 0:
        domain_match = any(
            hostname_lower == domain.lower() or hostname_lower.endswith("." + domain.lower())
            for domain in allowed_domains
        )
        if not domain_match:
            return False, f"Domain '{hostname}' is not in the allowed scrape domains list", None

    # 5. DNS Resolution & IP Checks
    try:
        # Resolve both IPv4 and IPv6 addresses
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        if not addr_info:
            return False, f"Could not resolve hostname '{hostname}'", None

        resolved_ips = set()
        for item in addr_info:
            sockaddr = item[4]
            ip_str = sockaddr[0]
            resolved_ips.add(ip_str)

        for ip in resolved_ips:
            safe, reason = is_ip_address_safe(ip)
            if not safe:
                return False, f"SSRF Protection: Hostname '{hostname}' resolved to blocked IP {ip} ({reason})", None

    except socket.gaierror as e:
        return False, f"DNS resolution failed for hostname '{hostname}': {str(e)}", None
    except Exception as e:
        return False, f"Error validating target host '{hostname}': {str(e)}", None

    canonical_url = f"{parsed.scheme.lower()}://{hostname_lower}{parsed.path or '/'}"
    if parsed.query:
        canonical_url += f"?{parsed.query}"

    return True, "URL verified safe", canonical_url


async def is_scraping_permitted_by_robots(url: str, user_agent: str = "PriceRadar/1.0") -> Tuple[bool, str]:
    """
    Checks target website's robots.txt to respect website restrictions and never bypass access controls.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # SSRF check robots_url itself before fetching
    safe, reason, _ = validate_url_ssrf_safe(robots_url)
    if not safe:
        return False, f"Cannot verify robots.txt due to safety restrictions: {reason}"

    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            resp = await client.get(robots_url, headers={"User-Agent": user_agent})
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
                allowed = rp.can_fetch(user_agent, url)
                if not allowed:
                    return False, f"Scraping disallowed by {parsed.netloc}/robots.txt for {parsed.path}"
                return True, "Permitted by robots.txt"
            elif resp.status_code in (401, 403):
                return False, f"Access restricted by robots.txt response code {resp.status_code}"
            else:
                # 404 or other: generally implies no robots restrictions
                return True, "No robots.txt restriction found"
    except Exception as e:
        # If robots.txt cannot be reached, default to cautious permit or log
        return True, f"Robots.txt check skipped (unreachable: {str(e)})"
