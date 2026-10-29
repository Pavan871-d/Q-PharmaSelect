"""
CSV Ingestion and Provenance Tracking Service.
Handles flexible column mapping, molecular validation, canonicalization,
deduplication, descriptor extraction, and detailed audit reporting.
"""

import io
import csv
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from ..chemistry.processor import chemistry_processor


# Standard expected field aliases for automatic column resolution
COLUMN_ALIASES = {
    "compound_id": ["compound_id", "id", "cmpd_id", "molecule_id", "internal_id"],
    "source_id": ["source_id", "chembl_id", "pubchem_id", "catalog_id", "compound_name", "name"],
    "smiles": ["smiles", "canonical_smiles", "input_smiles", "structure", "mol"],
    "cost": ["cost", "price", "assay_cost", "screening_cost", "cost_usd"],
    "availability": ["availability", "status", "available", "commercial_status"],
    "endpoint_value": ["endpoint_value", "ic50", "pic50", "activity", "value", "raw_value", "potency"],
    "endpoint_unit": ["endpoint_unit", "unit", "units"],
    "endpoint": ["endpoint", "endpoint_type", "assay_type", "metric"]
}


class CSVIngestionService:
    """Robust CSV ingestion and molecular audit pipeline."""

    def __init__(self):
        self.processor = chemistry_processor

    def resolve_columns(self, df_columns: List[str]) -> Dict[str, str]:
        """Maps uploaded dataframe column names to canonical schema keys."""
        mapping = {}
        lower_cols = {col.strip().lower(): col for col in df_columns}

        for canonical_name, aliases in COLUMN_ALIASES.items():
            for alias in aliases:
                if alias in lower_cols:
                    mapping[canonical_name] = lower_cols[alias]
                    break
        return mapping

    def parse_csv_file(
        self,
        file_content: bytes,
        filename: str = "upload.csv",
        user_column_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Parses CSV, validates structures, extracts chemical descriptors and scaffolds,
        deduplicates, and produces an audit report.
        """
        try:
            # Decode CSV with fallback encodings
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = file_content.decode("latin-1")

        df = pd.read_csv(io.StringIO(text))
        total_rows = len(df)

        # Merge user mapping with auto-detected mapping
        col_map = self.resolve_columns(list(df.columns))
        if user_column_mapping:
            col_map.update(user_column_mapping)

        if "smiles" not in col_map:
            raise ValueError(
                f"Missing required SMILES column. Uploaded columns: {list(df.columns)}. "
                f"Please map the SMILES structure column."
            )

        imported_records = []
        rejected_records = []
        seen_canonical_smiles = set()
        duplicated_count = 0

        for idx, row in df.iterrows():
            row_idx = idx + 1
            raw_smiles = str(row[col_map["smiles"]]).strip() if pd.notna(row[col_map["smiles"]]) else ""

            # Validate SMILES
            is_valid, canon_smiles, err = self.processor.validate_and_canonicalize(raw_smiles)
            if not is_valid:
                rejected_records.append({
                    "row": row_idx,
                    "input_smiles": raw_smiles,
                    "reason": err or "Invalid chemical structure."
                })
                continue

            # Deduplication
            if canon_smiles in seen_canonical_smiles:
                duplicated_count += 1
                rejected_records.append({
                    "row": row_idx,
                    "input_smiles": raw_smiles,
                    "canonical_smiles": canon_smiles,
                    "reason": "Duplicate canonical SMILES in uploaded dataset."
                })
                continue
            seen_canonical_smiles.add(canon_smiles)

            # Resolve identifiers
            compound_id = (
                str(row[col_map["compound_id"]]).strip()
                if "compound_id" in col_map and pd.notna(row[col_map["compound_id"]])
                else f"UP-{row_idx:04d}"
            )
            source_id = (
                str(row[col_map["source_id"]]).strip()
                if "source_id" in col_map and pd.notna(row[col_map["source_id"]])
                else compound_id
            )

            # Resolve cost
            try:
                cost = float(row[col_map["cost"]]) if "cost" in col_map and pd.notna(row[col_map["cost"]]) else 450.0
                if cost < 0:
                    cost = 450.0
            except (ValueError, TypeError):
                cost = 450.0

            # Resolve availability
            avail_raw = (
                str(row[col_map["availability"]]).strip().upper()
                if "availability" in col_map and pd.notna(row[col_map["availability"]])
                else "AVAILABLE"
            )
            if "UNAVAIL" in avail_raw or "OUT" in avail_raw or "FALSE" in avail_raw:
                availability = "UNAVAILABLE"
            elif "AVAIL" in avail_raw or "TRUE" in avail_raw or "YES" in avail_raw or "IN STOCK" in avail_raw:
                availability = "AVAILABLE"
            else:
                availability = "UNKNOWN"

            # Resolve endpoint value (e.g. IC50 or pIC50)
            raw_endpoint_val = None
            pic50_val = None
            unit = str(row[col_map["endpoint_unit"]]).strip() if "endpoint_unit" in col_map and pd.notna(row[col_map["endpoint_unit"]]) else "nM"

            if "endpoint_value" in col_map and pd.notna(row[col_map["endpoint_value"]]):
                try:
                    raw_val = float(row[col_map["endpoint_value"]])
                    raw_endpoint_val = raw_val
                    # Scientifically sound transformation
                    # If endpoint is already in pIC50 scale (typically 2 - 12)
                    if "pic50" in col_map["endpoint_value"].lower() or (unit.lower() in ["pic50", "-log10"]):
                        pic50_val = raw_val
                    elif unit.lower() in ["nm", "nanomolar"]:
                        if raw_val > 0:
                            import math
                            pic50_val = round(9.0 - math.log10(raw_val), 3)
                    elif unit.lower() in ["um", "micromolar"]:
                        if raw_val > 0:
                            import math
                            pic50_val = round(6.0 - math.log10(raw_val), 3)
                    elif unit.lower() in ["m", "molar"]:
                        if raw_val > 0:
                            import math
                            pic50_val = round(-math.log10(raw_val), 3)
                except (ValueError, TypeError):
                    pass

            # Molecular Descriptors & Scaffold Extraction
            desc = self.processor.calculate_descriptors(canon_smiles)
            scaffold_smiles, scaffold_id = self.processor.get_murcko_scaffold(canon_smiles)

            imported_records.append({
                "compound_id": compound_id,
                "source_id": source_id,
                "raw_smiles": raw_smiles,
                "canonical_smiles": canon_smiles,
                "molecular_formula": desc.get("molecular_formula"),
                "mw": desc.get("mw"),
                "logp": desc.get("logp"),
                "tpsa": desc.get("tpsa"),
                "hbd": desc.get("hbd"),
                "hba": desc.get("hba"),
                "rotatable_bonds": desc.get("rotatable_bonds"),
                "ring_count": desc.get("ring_count"),
                "scaffold": scaffold_smiles,
                "scaffold_id": scaffold_id,
                "cost": round(cost, 2),
                "availability": availability,
                "historical_pic50": pic50_val,
                "raw_endpoint_val": raw_endpoint_val,
                "endpoint_unit": unit,
                "evidence_status": "USER-PROVIDED DATA"
            })

        # Calculate 2D chemical space projection
        if imported_records:
            smiles_batch = [rec["canonical_smiles"] for rec in imported_records]
            coords_2d = self.processor.compute_chemical_space_2d(smiles_batch)
            for rec, (cx, cy) in zip(imported_records, coords_2d):
                rec["pca_x"] = cx
                rec["pca_y"] = cy

        return {
            "total_rows": total_rows,
            "imported_count": len(imported_records),
            "rejected_count": len(rejected_records),
            "duplicated_count": duplicated_count,
            "column_mapping": col_map,
            "records": imported_records,
            "rejected_details": rejected_records[:20]  # First 20 errors for user feedback
        }


csv_ingestion_service = CSVIngestionService()
