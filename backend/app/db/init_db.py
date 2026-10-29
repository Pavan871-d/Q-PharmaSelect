"""
Database initialization and seeding with verified ChEMBL EGFR library.
"""

from sqlalchemy.orm import Session
from ..db.session import engine, Base, SessionLocal
from ..models.entities import Target, Assay, Compound, AssayObservation
from ..services.data_ingestion.demo_data import EGFR_TARGET_INFO, EGFR_ASSAY_INFO, CURATED_COMPOUNDS
from ..services.chemistry.processor import chemistry_processor


def init_database():
    """Creates database tables and seeds curated EGFR dataset if empty."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if target exists
        target = db.query(Target).filter(Target.target_id == EGFR_TARGET_INFO["target_id"]).first()
        if not target:
            target = Target(**EGFR_TARGET_INFO)
            db.add(target)
            db.commit()

        # Check if assay exists
        assay = db.query(Assay).filter(Assay.assay_id == EGFR_ASSAY_INFO["assay_id"]).first()
        if not assay:
            assay = Assay(**EGFR_ASSAY_INFO)
            db.add(assay)
            db.commit()

        # Check if compounds exist
        comp_count = db.query(Compound).count()
        if comp_count == 0:
            print(f"Seeding database with {len(CURATED_COMPOUNDS)} curated compounds...")
            smiles_list = [c["smiles"] for c in CURATED_COMPOUNDS]
            coords = chemistry_processor.compute_chemical_space_2d(smiles_list)

            for idx, c in enumerate(CURATED_COMPOUNDS):
                desc = chemistry_processor.calculate_descriptors(c["smiles"])
                scaff_smiles, scaff_id = chemistry_processor.get_murcko_scaffold(c["smiles"])
                cx, cy = coords[idx] if idx < len(coords) else (0.0, 0.0)

                cmpd = Compound(
                    compound_id=c["compound_id"],
                    source_id=c["source_id"],
                    canonical_smiles=c["smiles"],
                    molecular_formula=desc.get("molecular_formula"),
                    mw=desc.get("mw"),
                    logp=desc.get("logp"),
                    tpsa=desc.get("tpsa"),
                    hbd=desc.get("hbd"),
                    hba=desc.get("hba"),
                    rotatable_bonds=desc.get("rotatable_bonds"),
                    ring_count=desc.get("ring_count"),
                    scaffold=scaff_smiles,
                    scaffold_id=scaff_id,
                    source_database="ChEMBL",
                    source_url=f"https://www.ebi.ac.uk/chembl/compound_report_card/{c['source_id']}/",
                    cost=c["cost"],
                    availability=c["availability"],
                    evidence_status=c["evidence_status"],
                    pca_x=cx,
                    pca_y=cy,
                    historical_pic50=c["historical_pic50"],
                    is_historical_hit=c["historical_pic50"] >= EGFR_ASSAY_INFO["activity_threshold_pic50"]
                )
                db.add(cmpd)

                obs = AssayObservation(
                    compound_id=c["compound_id"],
                    assay_id=EGFR_ASSAY_INFO["assay_id"],
                    endpoint="IC50",
                    raw_value=c["raw_ic50_nm"],
                    raw_unit="nM",
                    converted_pic50=c["historical_pic50"],
                    is_active=c["historical_pic50"] >= EGFR_ASSAY_INFO["activity_threshold_pic50"]
                )
                db.add(obs)

            db.commit()
            print("Curated compound seeding complete.")
    finally:
        db.close()

