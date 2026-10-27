"""
Unit Tests for Pydantic Schemas
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError
from app.schemas.product import ProductSubmissionRequest


def test_valid_product_submission():
    req = ProductSubmissionRequest(
        url="https://example.com/product/laptop-pro",
        target_price=Decimal("899.99"),
        user_email="user@example.com",
    )
    assert req.url == "https://example.com/product/laptop-pro"
    assert req.target_price == Decimal("899.99")
    assert req.notify_on_drop is True


def test_invalid_negative_target_price():
    with pytest.raises(ValidationError):
        ProductSubmissionRequest(
            url="https://example.com/product/laptop-pro",
            target_price=Decimal("-10.00"),
        )


def test_short_invalid_url():
    with pytest.raises(ValidationError):
        ProductSubmissionRequest(
            url="http://",
        )
