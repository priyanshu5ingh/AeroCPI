from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.api.v1.router import api_router
from app.db.session import engine
from app.models import Base

# Ensure tables exist on startup if running in simple standalone mode
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AeroCPI: Experimental Prototype Airfare Price Measurement Platform for CPI Augmentation",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Enable CORS for local dev / frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to AeroCPI Airfare Price Measurement API",
        "health_check": f"{settings.API_V1_STR}/health",
        "docs": "/docs"
    }
