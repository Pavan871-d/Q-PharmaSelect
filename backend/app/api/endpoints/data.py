"""
Compound Data Ingestion, Retrieval, and Provenance Endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from sqlalchemy.orm import Session
from ...db.session import get_db
from ...models.entities import Compound, Target, Assay, AssayObservation
from ...schemas.payloads import CompoundDetail, DatasetSummary
from ...services.data_ingestion.csv_parser import csv_ingestion_service

router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/summary", response_model=DatasetSummary)
def get_dataset_summary(db: Session = Depends(get_db)):
    """Returns dataset summary statistics and provenance breakdown."""
    compounds = db.query(Compound).all()
    total = len(compounds)
    if total == 0:
        return {
            "total_compounds": 0,
            "total_scaffolds": 0,
            "scaffold_diversity_ratio": 0.0,
            "total_observations": 0,
            "available_count": 0,
            "unavailable_count": 0,
            "unknown_availability_count": 0,
            "avg_cost": 0.0,
            "cost_range": [0.0, 0.0],
            "evidence_breakdown": {},
            "target": "None",
            "assay": "None"
        }

    scaffolds = set(c.scaffold_id for c in compounds if c.scaffold_id)
    avail = sum(1 for c in compounds if c.availability == "AVAILABLE")
    unavail = sum(1 for c in compounds if c.availability == "UNAVAILABLE")
    unknown = sum(1 for c in compounds if c.availability == "UNKNOWN")
    costs = [c.cost for c in compounds if c.cost is not None]
    avg_cost = sum(costs) / len(costs) if costs else 0.0
    cost_range = [min(costs), max(costs)] if costs else [0.0, 0.0]

    evidence_counts = {}
    for c in compounds:
        ev = c.evidence_status or "VERIFIED SOURCE DATA"
        evidence_counts[ev] = evidence_counts.get(ev, 0) + 1

    target = db.query(Target).first()
    assay = db.query(Assay).first()

    return {
        "total_compounds": total,
        "total_scaffolds": len(scaffolds),
        "scaffold_diversity_ratio": round(len(scaffolds) / total, 3),
        "total_observations": db.query(AssayObservation).count(),
        "available_count": avail,
        "unavailable_count": unavail,
        "unknown_availability_count": unknown,
        "avg_cost": round(avg_cost, 2),
        "cost_range": [round(cost_range[0], 2), round(cost_range[1], 2)],
        "evidence_breakdown": evidence_counts,
        "target": target.name if target else "EGFR",
        "assay": assay.assay_name if assay else "In vitro inhibition"
    }


@router.get("/compounds", response_model=List[CompoundDetail])
def get_compounds(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    scaffold_id: Optional[str] = None,
    availability: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Returns paginated compound candidates with optional search and filtering."""
    query = db.query(Compound)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Compound.compound_id.ilike(search_pattern)) |
            (Compound.source_id.ilike(search_pattern)) |
            (Compound.canonical_smiles.ilike(search_pattern))
        )
    if scaffold_id:
        query = query.filter(Compound.scaffold_id == scaffold_id)
    if availability:
        query = query.filter(Compound.availability == availability)

    return query.offset(skip).limit(limit).all()


@router.get("/compounds/{compound_id}", response_model=CompoundDetail)
def get_compound_detail(compound_id: str, db: Session = Depends(get_db)):
    """Returns full details and provenance record for a specific compound."""
    cmpd = db.query(Compound).filter(Compound.compound_id == compound_id).first()
    if not cmpd:
        raise HTTPException(status_code=404, detail=f"Compound {compound_id} not found.")
    return cmpd


@router.post("/upload")
async def upload_dataset_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a user CSV file, validates SMILES, deduplicates,
    calculates chemical descriptors & scaffolds, and imports into the database.
    """
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    try:
        result = csv_ingestion_service.parse_csv_file(content, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {str(e)}")

    # Persist validated records
    for rec in result["records"]:
        existing = db.query(Compound).filter(Compound.canonical_smiles == rec["canonical_smiles"]).first()
        if existing:
            continue

        cmpd = Compound(
            compound_id=rec["compound_id"],
            source_id=rec["source_id"],
            canonical_smiles=rec["canonical_smiles"],
            molecular_formula=rec["molecular_formula"],
            mw=rec["mw"],
            logp=rec["logp"],
            tpsa=rec["tpsa"],
            hbd=rec["hbd"],
            hba=rec["hba"],
            rotatable_bonds=rec["rotatable_bonds"],
            ring_count=rec["ring_count"],
            scaffold=rec["scaffold"],
            scaffold_id=rec["scaffold_id"],
            cost=rec["cost"],
            availability=rec["availability"],
            evidence_status="USER-PROVIDED DATA",
            pca_x=rec.get("pca_x", 0.0),
            pca_y=rec.get("pca_y", 0.0),
            historical_pic50=rec.get("historical_pic50")
        )
        db.add(cmpd)

    db.commit()

    return {
        "status": "SUCCESS",
        "filename": file.filename,
        "total_rows_read": result["total_rows"],
        "imported_count": result["imported_count"],
        "rejected_count": result["rejected_count"],
        "duplicated_count": result["duplicated_count"],
        "column_mapping": result["column_mapping"],
        "rejections": result["rejected_details"]
    }

