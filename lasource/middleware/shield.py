import uuid
import logging
import time
import re
from typing import Dict, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# iterate_in_threadpool is required to safely consume and rebuild the response body in Starlette
from starlette.concurrency import iterate_in_threadpool 

logger = logging.getLogger("lasource.audit")

class RateLimiter:
    """Tier-3 Ready in-memory Token Bucket rate limiter (can be swapped for Redis in prod)."""
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate # tokens per second
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        if client_id not in self.buckets:
            self.buckets[client_id] = (self.capacity - 1, now)
            return True

        tokens, last_refill = self.buckets[client_id]
        
        elapsed = now - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= 1:
            self.buckets[client_id] = (tokens - 1, now)
            return True
        
        self.buckets[client_id] = (tokens, now)
        return False

# High-availability / Tier-3 scaling limits
rate_limiter = RateLimiter(capacity=100, refill_rate=20.0)

class EntraIDValidator:
    @staticmethod
    def validate_jwt(token: str) -> bool:
        # Stub: Validate JWT with Azure AD keys using MSAL / PyJWT
        return True

class PIISanitizer:
    # Comprehensive regex patterns for common PII
    PATTERNS = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
        "PHONE": r'\b\+?1?\s*\(?-*\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b'
    }

    @staticmethod
    def run_pipeline(text: str) -> Tuple[bool, str]:
        """
        Runs the sanitization pipeline.
        Returns (is_allowed: bool, processed_text: str)
        """
        # Keyword Blocking - immediately reject if found
        forbidden_keywords = ["top secret", "confidential", "internal_use_only"]
        if any(keyword in text.lower() for keyword in forbidden_keywords):
            return False, text

        # PII Redaction - mask sensitive data but allow the request to proceed
        redacted_text = text
        for pii_type, pattern in PIISanitizer.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[REDACTED {pii_type}]", redacted_text)

        return True, redacted_text

class ShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 0. Azure Tier-3 Rate Limiting based on IP or UserToken (DDoS mitigation logic)
        client_ip = request.client.host if request.client else "127.0.0.1"
        if not rate_limiter.is_allowed(client_ip):
            logger.warning(
                "RateLimitExceeded",
                extra={"provider": "lasource-shield", "client_ip": client_ip}
            )
            return JSONResponse(status_code=429, content={"error": "Too Many Requests. Rate limit exceeded."})

        # 1. Attach Correlation ID for end-to-end tracing (OpenTelemetry readiness)
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # 2. Validate Entra ID JWT (Managed Identity & RBAC)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"error": "Missing or invalid authorization header"})
            
        token = auth_header.split(" ")[1]
        if not EntraIDValidator.validate_jwt(token):
            return JSONResponse(status_code=403, content={"error": "Invalid Entra ID Token"})

        # 3. Request Sanitization Pipeline
        if request.method in ["POST", "PUT"]:
            body_bytes = await request.body()
            if body_bytes:
                body_text = body_bytes.decode("utf-8")
                
                is_allowed, redacted_text = PIISanitizer.run_pipeline(body_text)
                
                if not is_allowed:
                    logger.warning(
                        "SecurityViolation",
                        extra={
                            "provider": "lasource-shield",
                            "correlation_id": correlation_id,
                            "reason": "Keyword Blocked"
                        }
                    )
                    return JSONResponse(status_code=400, content={"error": "Request blocked by Sanitization Pipeline."})
                
                # [AUDIT LOGGING] Log the safely redacted body. Never log the raw body_text!
                logger.info(
                    "RequestSanitized", 
                    extra={
                        "provider": "lasource-shield",
                        "correlation_id": correlation_id, 
                        "redacted_payload": redacted_text
                    }
                )
                
                # Inject redacted body back into the request pipeline
                redacted_bytes = redacted_text.encode("utf-8")
                async def receive_redacted():
                    return {"type": "http.request", "body": redacted_bytes}
                request._receive = receive_redacted

        # 4. Process the downstream provider request
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error("ProviderError", extra={"correlation_id": correlation_id, "error": str(e)})
            raise

        # 5. Response Pipeline Audit (Check for PII leakage from the provider)
        response_body = [chunk async for chunk in response.body_iterator]
        response.body_iterator = iterate_in_threadpool(iter(response_body)) # Reconstruct the iter so the client still gets it
        
        final_body_text = b"".join(response_body).decode("utf-8", errors="ignore")
        
        # We apply the scrubber to the response as well. We don't block, but we audit what we received.
        # Alternatively, we could actively replace the response body with safe text here.
        _, redacted_response_text = PIISanitizer.run_pipeline(final_body_text)
        
        # [AUDIT LOGGING] Safely log the final, scrubbed response
        logger.info(
            "ResponseProcessed",
            extra={
                "provider": "lasource-shield",
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "redacted_response": redacted_response_text
            }
        )

        response.headers["X-Correlation-ID"] = correlation_id
        return response
