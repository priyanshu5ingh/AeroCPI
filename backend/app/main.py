from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.models import Base

# Ensure tables exist on startup only if running local sqlite
if "sqlite" in settings.sync_database_url:
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AeroCPI: Experimental Prototype Airfare Price Measurement Platform for CPI Augmentation",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Parse CORS origins
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "AeroCPI API is healthy"}

@app.get("/")
def root():
    return {
        "message": "Welcome to AeroCPI Airfare Price Measurement API",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs"
    }
