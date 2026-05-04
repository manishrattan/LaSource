from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.lavoie.application.middleware.shield import ShieldMiddleware
from src.lavoie.infrastructure.factory import ProviderFactory
from lasource.domain.exceptions import (
    LaSourceException,
    LaSourceHealthCheckError,
    LaSourceProviderError
)
import logging
import os

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="LaSource AI Governance Shield",
    description="Enterprise-grade AI Governance Framework",
    version="1.0.0"
)

# Add CORS middleware for development/testing
# IMPORTANT: Configure CORS properly for production environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Attach the Shield Middleware
app.add_middleware(ShieldMiddleware)


@app.get("/healthz")
async def health_check():
    """
    Health check endpoint to verify provider connectivity.
    
    Returns:
        dict: Status information including provider name and health status.
        
    Response codes:
        200: Provider is healthy and reachable
        503: Provider is unhealthy or unreachable
        500: Internal error checking provider health
    """
    try:
        provider = ProviderFactory.get_provider()
        
        try:
            is_healthy = provider.health_check()
            
            if is_healthy:
                logger.info(f"Health check passed for provider: {provider.__class__.__name__}")
                return {
                    "status": "healthy",
                    "provider": provider.__class__.__name__
                }
            else:
                logger.warning(f"Health check failed for provider: {provider.__class__.__name__}")
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "unhealthy",
                        "provider": provider.__class__.__name__,
                        "error": f"{provider.__class__.__name__} health check failed."
                    }
                )
                
        except LaSourceHealthCheckError as e:
            logger.warning(f"Health check error: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "error": e.to_dict()
                }
            )
            
    except LaSourceProviderError as e:
        logger.error(f"Provider error during health check: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": e.to_dict()
            }
        )
    except LaSourceException as e:
        logger.error(f"LaSource error during health check: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": e.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error during health check: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error during health check"
            }
        )


@app.exception_handler(LaSourceException)
async def lasource_exception_handler(request: Request, exc: LaSourceException):
    """
    Global exception handler for all LaSource exceptions.
    
    Provides consistent error responses across the application.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        f"LaSource exception: {exc.error_code}",
        extra={
            "correlation_id": correlation_id,
            "error": str(exc)
        }
    )
    
    status_code = {
        "CONFIG_ERROR": 500,
        "PROVIDER_ERROR": 502,
        "AUTHENTICATION_ERROR": 403,
        "SECURITY_ERROR": 400,
        "VALIDATION_ERROR": 400,
        "HEALTH_CHECK_ERROR": 503,
        "RATE_LIMIT_ERROR": 429,
    }.get(exc.error_code, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "correlation_id": correlation_id
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unexpected errors.
    
    Provides safe error responses without exposing internal details.
    """
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.error(
        f"Unexpected error: {type(exc).__name__}",
        extra={
            "correlation_id": correlation_id,
            "error": str(exc)
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Internal server error",
            "correlation_id": correlation_id
        }
    )


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    
    Performs initialization checks and logs startup information.
    """
    logger.info("LaSource AI Governance Shield starting up...")
    
    try:
        provider = ProviderFactory.get_provider()
        logger.info(f"Provider initialized: {provider.__class__.__name__}")
    except LaSourceException as e:
        logger.warning(f"Provider initialization warning at startup: {str(e)}")
    except Exception as e:
        logger.warning(f"Unexpected error during provider initialization: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Shutdown event handler.
    
    Performs cleanup operations.
    """
    logger.info("LaSource AI Governance Shield shutting down...")
