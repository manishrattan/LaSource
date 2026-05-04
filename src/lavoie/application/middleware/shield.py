import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from lavoie.domain.services.scrubber import PIIScrubber
from starlette.concurrency import iterate_in_threadpool

# Example of setting up Azure Application Insights
from opencensus.ext.azure.log_exporter import AzureLogHandler

logger = logging.getLogger("lavoie.audit")
# In production, configure connection string via env var
# logger.addHandler(AzureLogHandler(connection_string='InstrumentationKey=...'))

class ShieldMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Call Domain Logic from Application Layer
        if request.method in ["POST", "PUT"]:
            body_bytes = await request.body()
            if body_bytes:
                body_text = body_bytes.decode("utf-8")
                
                is_allowed, redacted_text = PIIScrubber.sanitize(body_text)
                
                if not is_allowed:
                    logger.warning(
                        "SecurityViolation",
                        extra={
                            "provider": "lavoie-shield",
                            "correlation_id": correlation_id,
                            "reason": "Keyword Blocked"
                        }
                    )
                    return JSONResponse(status_code=400, content={"error": "Request blocked by Sanitization Pipeline."})
                
                # Persistent Audit Log: Sanitized Request
                logger.info(
                    "OutboundRequest",
                    extra={
                        "provider": "lavoie-shield",
                        "correlation_id": correlation_id,
                        "sanitized_payload": redacted_text
                    }
                )
                
                redacted_bytes = redacted_text.encode("utf-8")
                async def receive_redacted():
                    return {"type": "http.request", "body": redacted_bytes}
                request._receive = receive_redacted

        response = await call_next(request)
        
        if hasattr(response, 'body_iterator'):
            response_body = [chunk async for chunk in response.body_iterator]
            response.body_iterator = iterate_in_threadpool(iter(response_body))
            
            final_body_text = b"".join(response_body).decode("utf-8", errors="ignore")
            _, redacted_response_text = PIIScrubber.sanitize(final_body_text)
            
            # Persistent Audit Log: Sanitized Response
            logger.info(
                "InboundResponse",
                extra={
                    "provider": "lavoie-shield",
                    "correlation_id": correlation_id,
                    "status_code": response.status_code,
                    "sanitized_response": redacted_response_text
                }
            )

        response.headers["X-Correlation-ID"] = correlation_id
        return response
