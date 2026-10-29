"""
PubChem PUG-REST API Adapter for Q-PharmaSelect.

Provides external compound resolution, fetching canonical SMILES, IUPAC names,
molecular weights, and chemical properties from NCBI PubChem.
Includes offline fallback mode and timeout guards.
"""

from typing import Dict, Any, Optional
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger(__name__)

PUG_REST_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"


class PubChemAdapter:
    """Interface to NCBI PubChem REST services with robust error handling."""

    @staticmethod
    def get_compound_by_name(name: str, timeout_sec: int = 4) -> Optional[Dict[str, Any]]:
        """
        Query PubChem by chemical or common name (e.g. 'Osimertinib', 'Gefitinib').
        Returns dictionary with SMILES, molecular formula, weight, and InChIKey.
        """
        encoded_name = urllib.parse.quote(name.strip())
        url = (
            f"{PUG_REST_BASE}/compound/name/{encoded_name}/property/"
            "CanonicalSMILES,IsomericSMILES,MolecularWeight,MolecularFormula,IUPACName,InChIKey,XLogP/JSON"
        )
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Q-PharmaSelect/1.0 (DrugDiscoveryDecisionSupport)"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    if props:
                        item = props[0]
                        return {
                            "cid": item.get("CID"),
                            "name": name,
                            "smiles": item.get("CanonicalSMILES") or item.get("IsomericSMILES"),
                            "molecular_weight": item.get("MolecularWeight"),
                            "molecular_formula": item.get("MolecularFormula"),
                            "iupac_name": item.get("IUPACName"),
                            "inchikey": item.get("InChIKey"),
                            "logp": item.get("XLogP"),
                            "source": "PubChem PUG-REST"
                        }
        except Exception as e:
            logger.warning("PubChem resolution failed for '%s': %s", name, str(e))
            return None
        return None

    @staticmethod
    def get_compound_by_cid(cid: int, timeout_sec: int = 4) -> Optional[Dict[str, Any]]:
        """Query PubChem by Compound Identifier (CID)."""
        url = (
            f"{PUG_REST_BASE}/compound/cid/{cid}/property/"
            "CanonicalSMILES,IsomericSMILES,MolecularWeight,MolecularFormula,IUPACName,InChIKey,XLogP/JSON"
        )
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Q-PharmaSelect/1.0 (DrugDiscoveryDecisionSupport)"}
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    props = data.get("PropertyTable", {}).get("Properties", [])
                    if props:
                        item = props[0]
                        return {
                            "cid": item.get("CID"),
                            "name": f"PubChem-CID-{cid}",
                            "smiles": item.get("CanonicalSMILES") or item.get("IsomericSMILES"),
                            "molecular_weight": item.get("MolecularWeight"),
                            "molecular_formula": item.get("MolecularFormula"),
                            "iupac_name": item.get("IUPACName"),
                            "inchikey": item.get("InChIKey"),
                            "logp": item.get("XLogP"),
                            "source": "PubChem PUG-REST"
                        }
        except Exception as e:
            logger.warning("PubChem resolution failed for CID %s: %s", cid, str(e))
            return None
        return None

