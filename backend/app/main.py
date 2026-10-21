from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API powering the E-Commerce Decision Intelligence Cockpit, Lakehouse KPIs, and NLP Review Analytics.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Also mount at /api for seamless backward compatibility
app.include_router(api_router, prefix="/api")


@app.get("/health")
def health_check():
    """Service health check endpoint."""
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/")
def root():
    return {
        "message": "Welcome to the E-Commerce Decision Intelligence Platform API",
        "docs": "/docs",
        "health": "/health"
    }
