"""
Root API Router combining all domain endpoint modules.
"""

from fastapi import APIRouter
from .endpoints.targets import router as targets_router
from .endpoints.data import router as data_router
from .endpoints.models import router as models_router
from .endpoints.quantum import router as quantum_router
from .endpoints.optimization import router as optimization_router
from .endpoints.validation import router as validation_router
from .endpoints.reports import router as reports_router
from .endpoints.integrations import router as integrations_router

api_router = APIRouter()

api_router.include_router(targets_router)
api_router.include_router(data_router)
api_router.include_router(models_router)
api_router.include_router(quantum_router)
api_router.include_router(optimization_router)
api_router.include_router(validation_router)
api_router.include_router(reports_router)
api_router.include_router(integrations_router)

