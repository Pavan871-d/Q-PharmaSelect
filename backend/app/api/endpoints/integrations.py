"""
Integrations and External Service Status Endpoints.
Manages QpiAI QCloud and QpiAI Opt connection state and environment diagnostics.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter
from ...core.config import settings
from ...services.quantum.qcloud_runner import quantum_service
from ...services.optimization.solver_adapter import opt_service

router = APIRouter(prefix="/integrations", tags=["Integrations & Settings"])


class ConfigUpdatePayload(BaseModel):
    qpiai_qcloud_api_key: Optional[str] = None
    qpiai_opt_api_key: Optional[str] = None
    qpiai_opt_url: Optional[str] = None


@router.get("/status")
def get_integrations_status() -> Dict[str, Any]:
    """Returns real-time connection status for all external quantum and optimization backends."""
    qcloud_status = quantum_service.check_connection()
    opt_status = opt_service.check_connection()

    import rdkit
    import sklearn
    import fastapi

    return {
        "qcloud": qcloud_status,
        "qpiai_opt": opt_status,
        "runtime_environment": {
            "environment": settings.ENVIRONMENT,
            "database_url": settings.DATABASE_URL.split("///")[-1] if "///" in settings.DATABASE_URL else "configured",
            "python_packages": {
                "qpiai_quantum": quantum_service.sdk_version,
                "qpiai_opt_api": "1.0.6",
                "rdkit": rdkit.__version__,
                "scikit_learn": sklearn.__version__,
                "fastapi": fastapi.__version__
            }
        }
    }


@router.post("/config")
def update_credentials(payload: ConfigUpdatePayload):
    """Updates API keys securely in memory during session."""
    updated = []
    if payload.qpiai_qcloud_api_key is not None:
        settings.QPIAI_QCLOUD_API_KEY = payload.qpiai_qcloud_api_key.strip()
        updated.append("QPIAI_QCLOUD_API_KEY")
    if payload.qpiai_opt_api_key is not None:
        settings.QPIAI_OPT_API_KEY = payload.qpiai_opt_api_key.strip()
        updated.append("QPIAI_OPT_API_KEY")
    if payload.qpiai_opt_url is not None:
        settings.QPIAI_OPT_URL = payload.qpiai_opt_url.strip()
        updated.append("QPIAI_OPT_URL")

    return {
        "status": "UPDATED",
        "fields_updated": updated,
        "has_qcloud_key": settings.has_qcloud_key,
        "has_opt_key": settings.has_opt_key
    }

