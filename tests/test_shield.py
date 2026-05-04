import pytest
from lasource.middleware.shield import PIISanitizer, rate_limiter

def test_pii_sanitizer_blocks_keywords():
    is_allowed, text = PIISanitizer.run_pipeline("This is top secret data.")
    assert not is_allowed

def test_pii_sanitizer_redacts_email():
    is_allowed, text = PIISanitizer.run_pipeline("Contact me at user@example.com")
    assert is_allowed
    assert "[REDACTED EMAIL]" in text
    assert "user@example.com" not in text

def test_rate_limiter_allows_under_limit():
    assert rate_limiter.is_allowed("127.0.0.1")
    assert rate_limiter.is_allowed("127.0.0.1")
