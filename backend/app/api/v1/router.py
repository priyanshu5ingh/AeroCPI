from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    observation_explorer,
    observations,
    virtual_trips,
    route_intelligence,
    routes,
    carriers,
    sources,
    index_runs,
    measurement_trace,
    publication_readiness,
    reference_data,
    dgca_reference,
    trust_evaluations,
    measurement_configurations,
    horizon_intelligence,
    data_quality,
    methodology_info,
    validation_lab,
    aeroguide,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(observation_explorer.router, tags=["Observation Explorer"])
api_router.include_router(observations.router, tags=["Observations"])
api_router.include_router(virtual_trips.router, tags=["Virtual Trips"])
api_router.include_router(route_intelligence.router, tags=["Route Intelligence"])
api_router.include_router(routes.router, tags=["Routes"])
api_router.include_router(carriers.router, tags=["Carriers"])
api_router.include_router(sources.router, tags=["Sources"])
api_router.include_router(measurement_trace.router, tags=["Measurement Trace Engine"])
api_router.include_router(publication_readiness.router, tags=["Publication Readiness"])
api_router.include_router(index_runs.router, tags=["Index Runs"])
api_router.include_router(reference_data.router, tags=["Official Reference Data"])
api_router.include_router(dgca_reference.router, tags=["DGCA Traffic Reference Data"])
api_router.include_router(trust_evaluations.router, tags=["Trust Engine"])
api_router.include_router(measurement_configurations.router, tags=["Measurement Configurations"])
api_router.include_router(horizon_intelligence.router, tags=["Horizon Intelligence"])
api_router.include_router(data_quality.router, tags=["Data Quality Intelligence"])
api_router.include_router(methodology_info.router, tags=["Methodology Studio"])
api_router.include_router(validation_lab.router, tags=["Validation Lab"])
api_router.include_router(aeroguide.router, tags=["AeroGuide Consumer Intelligence"])

