"""
Main FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sentry_sdk
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.router import api_router
from app.core.logging_config import setup_logging

# Setup logging
setup_logging()

# Initialize Sentry (if configured)
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        traces_sample_rate=1.0 if settings.ENVIRONMENT == "development" else 0.1,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print("🚀 Starting Micro Gallery Japan API...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🔧 Debug Mode: {settings.DEBUG}")
    print(f"📍 API Version: {settings.API_VERSION}")
    
    # TODO: Initialize ML models here
    # TODO: Setup Redis connection pool
    # TODO: Verify Supabase connection
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Micro Gallery Japan API...")
    # TODO: Cleanup resources


# Create FastAPI app
app = FastAPI(
    title="Micro Gallery Japan API",
    description="Backend API for artwork marketplace platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=f"/api/{settings.API_VERSION}/docs",
    redoc_url=f"/api/{settings.API_VERSION}/redoc",
    openapi_url=f"/api/{settings.API_VERSION}/openapi.json",
)


# Customize OpenAPI schema to include security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    from fastapi.openapi.utils import get_openapi
    from app.core.dependencies import security
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme - the key must match what HTTPBearer uses
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {}
    
    # HTTPBearer with scheme_name="BearerAuth" uses "BearerAuth" as the key
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token. You can get it from the login endpoint. Just paste the token value (without 'Bearer' prefix).",
    }
    
    # Also add as "Bearer" for compatibility
    openapi_schema["components"]["securitySchemes"]["Bearer"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token. You can get it from the login endpoint. Just paste the token value (without 'Bearer' prefix).",
    }
    
    # Add security requirement to paths that use get_current_user
    # This tells Swagger UI to include the Authorization header
    if "paths" in openapi_schema:
        for path, methods in openapi_schema["paths"].items():
            for method, details in methods.items():
                if isinstance(details, dict):
                    # Check if this endpoint has get_current_user in dependencies
                    # We'll add security to all endpoints that might need it
                    # The user can test and we'll refine
                    if "security" not in details:
                        # Don't add security automatically - let FastAPI handle it
                        pass
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS Configuration
# Parse CORS_ORIGINS from settings (comma-separated string)
cors_origins = [
    origin.strip() 
    for origin in settings.CORS_ORIGINS.split(",") 
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],
    expose_headers=["*"],
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - Health check"""
    return JSONResponse(
        content={
            "message": "Micro Gallery Japan API",
            "version": "0.1.0",
            "environment": settings.ENVIRONMENT,
            "docs": f"/api/{settings.API_VERSION}/docs",
        }
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "environment": settings.ENVIRONMENT,
        }
    )


# Include API router
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
