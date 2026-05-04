from fastapi import FastAPI
from fastapi.responses import JSONResponse
from lavoie.application.middleware.shield import ShieldMiddleware
from lavoie.infrastructure.factory import ProviderFactory
import logging

app = FastAPI(title="LaSource AI Governance Shield")

# Attach the Shield Middleware
app.add_middleware(ShieldMiddleware)

@app.get("/healthz")
async def health_check():
    """Health check endpoint to verify provider connectivity."""
    try:
        provider = ProviderFactory.get_provider()
        is_healthy = provider.health_check()
        
        if is_healthy:
            return {"status": "healthy", "provider": provider.__class__.__name__}
        else:
            return JSONResponse(
                status_code=503, 
                content={"status": "unhealthy", "error": f"{provider.__class__.__name__} health check failed."}
            )
    except Exception as e:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "error": str(e)})
