"""
Application Configuration for Q-PharmaSelect.
Manages environment variables, secrets, and system constants.
"""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR.parent / "data"
REPORTS_DIR = BASE_DIR.parent / "reports"
EXPERIMENTS_DIR = BASE_DIR.parent / "experiments"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseModel):
    APP_NAME: str = "Q-PharmaSelect"
    APP_VERSION: str = "1.0.0"
    TAGLINE: str = "Quantum-Enhanced Molecular Discovery and Intelligent Assay Selection"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = os.getenv("APP_ENV", "development")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR.parent}/qpharmaselect.db")

    # QpiAI Technologies Credentials & Endpoints
    QPIAI_QCLOUD_API_KEY: str = os.getenv("QPIAI_QCLOUD_API_KEY", "")
    QPIAI_OPT_API_KEY: str = os.getenv("QPIAI_OPT_API_KEY", "")
    QPIAI_OPT_URL: str = os.getenv("QPIAI_OPT_URL", "https://opt.qpiai.tech")

    # Security & CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "*"
    ]

    # Defaults for Compound Selection
    DEFAULT_BATCH_SIZE: int = 15
    DEFAULT_BUDGET: float = 12000.0
    DEFAULT_CURRENCY: str = "USD"
    DEFAULT_ACTIVITY_THRESHOLD_PIC50: float = 6.5  # pIC50 >= 6.5 (~316 nM) is active hit

    @property
    def has_qcloud_key(self) -> bool:
        return bool(self.QPIAI_QCLOUD_API_KEY and self.QPIAI_QCLOUD_API_KEY.strip())

    @property
    def has_opt_key(self) -> bool:
        return bool(self.QPIAI_OPT_API_KEY and self.QPIAI_OPT_API_KEY.strip())


settings = Settings()

