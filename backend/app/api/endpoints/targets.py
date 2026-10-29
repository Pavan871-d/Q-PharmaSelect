"""
Target and Assay Configuration Endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Target, Assay
from ...schemas.payloads import TargetCreate, TargetResponse, AssayCreate, AssayResponse

router = APIRouter(prefix="/targets", tags=["Targets & Assays"])


@router.get("", response_model=List[TargetResponse])
def list_targets(db: Session = Depends(get_db)):
    return db.query(Target).all()


@router.post("", response_model=TargetResponse)
def create_target(payload: TargetCreate, db: Session = Depends(get_db)):
    existing = db.query(Target).filter(Target.target_id == payload.target_id).first()
    if existing:
        for k, v in payload.dict().items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    target = Target(**payload.dict())
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


@router.get("/assays", response_model=List[AssayResponse])
def list_assays(db: Session = Depends(get_db)):
    return db.query(Assay).all()


@router.post("/assays", response_model=AssayResponse)
def create_assay(payload: AssayCreate, db: Session = Depends(get_db)):
    existing = db.query(Assay).filter(Assay.assay_id == payload.assay_id).first()
    if existing:
        for k, v in payload.dict().items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return existing

    assay = Assay(**payload.dict())
    db.add(assay)
    db.commit()
    db.refresh(assay)
    return assay

