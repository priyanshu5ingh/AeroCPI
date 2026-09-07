from fastapi import APIRouter
from app.api.v1.endpoints import health, observations, virtual_trips, routes, carriers, sources

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(observations.router, tags=["Observations"])
api_router.include_router(virtual_trips.router, tags=["Virtual Trips"])
api_router.include_router(routes.router, tags=["Routes"])
api_router.include_router(carriers.router, tags=["Carriers"])
api_router.include_router(sources.router, tags=["Sources"])
