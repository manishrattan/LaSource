import uuid
import logging
import time
import re
from typing import Dict, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from lasource.domain.exceptions import (
    LaSourceRateLimitError,
    LaSourceAuthenticationError,
    LaSourceSecurityError
)

# iterate_in_threadpool is required to safely consume and rebuild the response body in Starlette
from starlette.concurrency import iterate_in_threadpool 

logger = logging.getLogger("lasource.audit")


class RateLimiter:
    """
    Tier-3 Ready in-memory Token Bucket rate limiter.
    
    Can be swapped for Redis, Memcached, or other distributed systems in production.
    
    Args:
        capacity: Maximum number of tokens in the bucket.
        refill_rate: Number of tokens added per second.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than 0")
        if refill_rate <= 0:
            raise ValueError("Refill rate must be greater than 0")
            
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.buckets: Dict[str, Tuple[float, float]] = {}

    def is_allowed(self, client_id: str) -> bool:
        """
        Check if a client has tokens available.
        
        Args:
            client_id: Unique identifier for the client (IP, user ID, etc.).
            
        Returns:
            bool: True if request is allowed, False if rate limit exceeded.
            
        Raises:
            LaSourceRateLimitError: If rate limit check fails critically.
        """
        if not client_id:
            raise LaSourceRateLimitError("Client ID cannot be empty")
        
        try:
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
            
        except Exception as e:
            logger.error(f"Error in rate limiter: {str(e)}", exc_info=True)
            raise LaSourceRateLimitError(f"Rate limiting check failed: {str(e)}")


# High-availability / Tier-3 scaling limits
# Production: Consider using Redis-backed rate limiter
rate_limiter = RateLimiter(capacity=100, refill_rate=20.0)


class EntraIDValidator:
    """
    Validates JWT tokens issued by Azure Entra ID.
    
    This is a stub implementation. In production, validate against:
    - Microsoft's OpenID Connect endpoint
    - Cached public keys
    - Token expiration, issuer, audience claims
    """
    
    @staticmethod
    def validate_jwt(token: str) -> bool:
        """
        Validate JWT token from Azure Entra ID.
        
        Args:
            token: JWT token string.
            
        Returns:
            bool: True if token is valid.
            
        Raises:
            LaSourceAuthenticationError: If token validation fails.
        """
        if not token or not token.strip():
            raise LaSourceAuthenticationError("Token cannot be empty")
        
        try:
            # TODO: Implement real validation using PyJWT and Azure AD keys
            # 1. Decode token (without verification for now)
            # 2. Fetch public keys from https://login.microsoftonline.com/{tenantId}/discovery/v2.0/keys
            # 3. Verify signature
            # 4. Check expiration, issuer, audience
            
            # Stub: Just verify token is not empty
            return True
            
        except Exception as e:
            logger.error(f"JWT validation error: {str(e)}", exc_info=True)
            raise LaSourceAuthenticationError(f"JWT validation failed: {str(e)}")


class PIISanitizer:
    """
    Comprehensive PII and keyword detection/redaction pipeline.
    
    Patterns:
        EMAIL: Email addresses
        SSN: US Social Security Numbers
        CREDIT_CARD: Credit card numbers (PAN)
        PHONE: Phone numbers
    """
    
    # Comprehensive regex patterns for common PII
    PATTERNS = {
        "EMAIL": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        "SSN": r'\b\d{3}-\d{2}-\d{4}\b',
        "CREDIT_CARD": r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b',
        "PHONE": r'\b\+?1?\s*\(?-*\d{3}\)?[-.\s]*\d{3}[-.\s]*\d{4}\b'
    }
    
    FORBIDDEN_KEYWORDS = ["top secret", "confidential", "internal_use_only"]

    @staticmethod
    def run_pipeline(text: str) -> Tuple[bool, str]:
        """
        Runs the sanitization pipeline.
        
        1. Checks for forbidden keywords and BLOCKS request if found
        2. Scans for PII patterns and REDACTS them
        
        Args:
            text: Input text to sanitize.
            
        Returns:
            (is_allowed: bool, processed_text: str)
            - is_allowed: False if forbidden keywords found, True otherwise
            - processed_text: Text with PII redacted
            
        Raises:
            LaSourceSecurityError: If text contains restricted content.
        """
        if not text:
            return True, text
        
        try:
            # Keyword Blocking - immediately reject if found
            text_lower = text.lower()
            for keyword in PIISanitizer.FORBIDDEN_KEYWORDS:
                if keyword in text_lower:
                    raise LaSourceSecurityError(
                        f"Request blocked: Forbidden keyword detected: '{keyword}'",
                        violation_type="FORBIDDEN_KEYWORD"
                    )

            # PII Redaction - mask sensitive data but allow the request to proceed
            redacted_text = text
            for pii_type, pattern in PIISanitizer.PATTERNS.items():
                redacted_text = re.sub(pattern, f"[REDACTED {pii_type}]", redacted_text)

            return True, redacted_text
            
        except LaSourceSecurityError:
            raise
        except Exception as e:
            logger.error(f"Error in PII sanitizer: {str(e)}", exc_info=True)
            raise LaSourceSecurityError(f"PII sanitization failed: {str(e)}")


class ShieldMiddleware(BaseHTTPMiddleware):
    """
    Multi-layer security middleware for LaSource.
    
    Layers:
    1. Rate Limiting - Prevent DDoS attacks
    2. Correlation ID - Enable end-to-end tracing
    3. Authentication - Validate Azure Entra ID JWT
    4. Request Sanitization - Block keywords, redact PII
    5. Provider Routing - Forward to AI provider
    6. Response Audit - Log outbound responses
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Main middleware dispatch method.
        
        Args:
            request: Incoming HTTP request.
            call_next: Next middleware/handler in chain.
            
        Returns:
            Response with security headers and audit logging.
        """
        try:
            # 0. Azure Tier-3 Rate Limiting based on IP or UserToken (DDoS mitigation logic)
            client_ip = request.client.host if request.client else "127.0.0.1"
            try:
                if not rate_limiter.is_allowed(client_ip):
                    logger.warning(
                        "RateLimitExceeded",
                        extra={"provider": "lasource-shield", "client_ip": client_ip}
                    )
                    return JSONResponse(
                        status_code=429,
                        content={"error": "Too Many Requests", "message": "Rate limit exceeded."}
                    )
            except LaSourceRateLimitError as e:
                logger.error(f"Rate limiter error: {str(e)}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate Limit Error", "message": str(e)}
                )

            # 1. Attach Correlation ID for end-to-end tracing (OpenTelemetry readiness)
            correlation_id = str(uuid.uuid4())
            request.state.correlation_id = correlation_id
            
            # 2. Validate Entra ID JWT (Managed Identity & RBAC)
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning(
                    "MissingAuthHeader",
                    extra={"correlation_id": correlation_id, "client_ip": client_ip}
                )
                return JSONResponse(status_code=401, content={"error": "Missing or invalid authorization header"})
            
            try:
                token = auth_header.split(" ")[1]
                EntraIDValidator.validate_jwt(token)
            except LaSourceAuthenticationError as e:
                logger.warning(
                    "AuthenticationFailure",
                    extra={"correlation_id": correlation_id, "error": str(e)}
                )
                return JSONResponse(status_code=403, content={"error": "Invalid Entra ID Token"})
            except Exception as e:
                logger.error(f"Authentication error: {str(e)}", exc_info=True)
                return JSONResponse(status_code=403, content={"error": "Authentication failed"})

            # 3. Request Sanitization Pipeline
            if request.method in ["POST", "PUT"]:
                try:
                    body_bytes = await request.body()
                    if body_bytes:
                        body_text = body_bytes.decode("utf-8", errors="replace")
                        
                        try:
                            is_allowed, redacted_text = PIISanitizer.run_pipeline(body_text)
                        except LaSourceSecurityError as e:
                            logger.warning(
                                "SecurityViolation",
                                extra={
                                    "correlation_id": correlation_id,
                                    "error": str(e),
                                    "client_ip": client_ip
                                }
                            )
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Security Policy Violation", "message": str(e)}
                            )
                        
                        if not is_allowed:
                            logger.warning(
                                "SecurityViolation",
                                extra={
                                    "provider": "lasource-shield",
                                    "correlation_id": correlation_id,
                                    "reason": "Keyword Blocked"
                                }
                            )
                            return JSONResponse(
                                status_code=400,
                                content={"error": "Request blocked by Sanitization Pipeline."}
                            )
                        
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
                        
                except Exception as e:
                    logger.error(f"Error processing request body: {str(e)}", exc_info=True)
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Request processing failed"}
                    )

            # 4. Process the downstream provider request
            try:
                response = await call_next(request)
            except Exception as e:
                logger.error(
                    "ProviderError",
                    extra={"correlation_id": correlation_id, "error": str(e)},
                    exc_info=True
                )
                return JSONResponse(
                    status_code=502,
                    content={"error": "Provider Error", "message": "Failed to reach AI provider"}
                )

            # 5. Response Pipeline Audit (Check for PII leakage from the provider)
            try:
                response_body = [chunk async for chunk in response.body_iterator]
                response.body_iterator = iterate_in_threadpool(iter(response_body))
                
                final_body_text = b"".join(response_body).decode("utf-8", errors="ignore")
                
                # We apply the scrubber to the response as well. We don't block, but we audit what we received.
                try:
                    _, redacted_response_text = PIISanitizer.run_pipeline(final_body_text)
                except LaSourceSecurityError as e:
                    logger.warning(
                        "ResponseSecurityIssue",
                        extra={
                            "correlation_id": correlation_id,
                            "message": "Response contains security violation pattern"
                        }
                    )
                    redacted_response_text = final_body_text
                
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
                
            except Exception as e:
                logger.error(f"Error processing response: {str(e)}", exc_info=True)

            response.headers["X-Correlation-ID"] = correlation_id
            return response
            
        except Exception as e:
            logger.error(f"Unexpected error in ShieldMiddleware: {str(e)}", exc_info=True)
            correlation_id = str(uuid.uuid4())
            return JSONResponse(
                status_code=500,
                content={"error": "Internal Server Error", "correlation_id": correlation_id}
            )
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
