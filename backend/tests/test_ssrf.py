"""
Unit Tests for SSRF Protection Module
Verifies that private subnets, loopbacks, cloud metadata, and invalid schemes are blocked.
"""

import pytest
from app.core.security import validate_url_ssrf_safe, is_ip_address_safe


def test_ip_address_safety_blocks_loopback():
    safe, reason = is_ip_address_safe("127.0.0.1")
    assert not safe
    assert "loopback" in reason.lower()

    safe_v6, reason_v6 = is_ip_address_safe("::1")
    assert not safe_v6
    assert "loopback" in reason_v6.lower()


def test_ip_address_safety_blocks_private_networks():
    # RFC 1918 ranges
    for private_ip in ["10.0.0.1", "172.16.0.1", "172.31.255.254", "192.168.1.1"]:
        safe, reason = is_ip_address_safe(private_ip)
        assert not safe, f"Should have blocked private IP {private_ip}"
        assert "private" in reason.lower()


def test_ip_address_safety_blocks_cloud_metadata():
    # AWS / GCP / Azure link-local metadata address
    safe, reason = is_ip_address_safe("169.254.169.254")
    assert not safe
    assert "link-local" in reason.lower() or "metadata" in reason.lower()


def test_validate_url_blocks_dangerous_schemes():
    dangerous_urls = [
        "file:///etc/passwd",
        "ftp://ftp.example.com/file",
        "gopher://gopher.example.com/",
        "javascript:alert(1)",
        "data:text/html,test",
    ]
    for url in dangerous_urls:
        safe, reason, _ = validate_url_ssrf_safe(url)
        assert not safe, f"Should have blocked dangerous scheme: {url}"
        assert "scheme" in reason.lower()


def test_validate_url_blocks_internal_hosts():
    internal_urls = [
        "http://localhost:8000/api",
        "http://127.0.0.1/admin",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://instance-data/latest/meta-data/",
    ]
    for url in internal_urls:
        safe, reason, _ = validate_url_ssrf_safe(url)
        assert not safe, f"Should have blocked internal target: {url}"


def test_validate_url_blocks_non_standard_ports():
    unusual_ports = [
        "http://example.com:22/ssh",
        "http://example.com:3306/mysql",
        "http://example.com:5432/postgres",
        "http://example.com:6379/redis",
    ]
    for url in unusual_ports:
        safe, reason, _ = validate_url_ssrf_safe(url)
        assert not safe, f"Should have blocked non-web port: {url}"
        assert "port" in reason.lower()
