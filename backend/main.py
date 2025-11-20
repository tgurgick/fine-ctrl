"""Fine-Tune Platform API."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import settings
from backend.middleware.rate_limiter import limiter

# Create FastAPI app
app = FastAPI(
    title="Fine-Tune Platform API",
    description="Agent-driven fine-tuning platform for custom models",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected",  # TODO: Add actual DB health check
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fine-Tune Platform API",
        "version": "0.1.0",
        "docs": "/docs",
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.ENVIRONMENT == "development" else None,
        },
    )


# Import and include routers
from backend.api.routes import auth, api_keys
# Note: Other routers will be implemented in later work packages
# from backend.api.routes import tasks, datasets, training, deployments

# WP-0.5: Authentication and API Key routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["api-keys"])

# Future routers (to be implemented in later work packages)
# app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
# app.include_router(datasets.router, prefix="/api/v1/datasets", tags=["datasets"])
# app.include_router(training.router, prefix="/api/v1/training", tags=["training"])
# app.include_router(deployments.router, prefix="/api/v1/deployments", tags=["deployments"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False,
    )
