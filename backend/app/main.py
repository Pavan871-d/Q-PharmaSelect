"""
Main FastAPI application entry point for Q-PharmaSelect.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .db.init_db import init_database
from .api.api import api_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Quantum-Enhanced Molecular Discovery and Intelligent Assay Selection API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initializes database schema and seeds curated EGFR target library."""
    try:
        init_database()
        print("Database schema verified and initial library seeded successfully.")
    except Exception as e:
        print(f"Warning during database initialization: {e}")


@app.get("/api/health", tags=["Health"])
def health_check():
    """System health check endpoint."""
    return {
        "status": "HEALTHY",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "tagline": settings.TAGLINE,
        "environment": settings.ENVIRONMENT
    }


# Include all modular API endpoints
app.include_router(api_router, prefix=settings.API_PREFIX)

# Static file serving for built React SPA
from pathlib import Path
from fastapi.staticfiles import StaticFiles
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

