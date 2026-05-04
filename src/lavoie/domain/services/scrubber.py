import re
from typing import Tuple, Dict

class PIIScrubber:
    """Domain service for redacting PII and internal keywords.
    Clean Architecture: This logic has zero dependencies on FastAPI or Azure.
    """
    
    PATTERNS: Dict[str, str] = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
        "PHONE": r'\b\+?1?\s*\(?-*\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b',
        "MAC_ADDRESS": r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b',
        "IP_ADDRESS": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
    }

    FORBIDDEN_KEYWORDS = ["top secret", "confidential", "internal_use_only"]

    @classmethod
    def sanitize(cls, text: str) -> Tuple[bool, str]:
        """
        Runs the sanitization pipeline.
        Returns (is_allowed: bool, processed_text: str)
        """
        if any(keyword in text.lower() for keyword in cls.FORBIDDEN_KEYWORDS):
            return False, text

        redacted_text = text
        for pii_type, pattern in cls.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED {pii_type}]", redacted_text)

        return True, redacted_text
