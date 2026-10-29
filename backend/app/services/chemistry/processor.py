"""
Cheminformatics processing engine powered by RDKit.
Handles SMILES validation, canonicalization, descriptor calculation,
ECFP4 Morgan fingerprints, Bemis-Murcko scaffolds, and Tanimoto similarity.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from sklearn.decomposition import PCA

try:
    from rdkit import Chem, RDLogger
    from rdkit.Chem import Descriptors, AllChem, rdMolDescriptors
    from rdkit.Chem.Scaffolds import MurckoScaffold
    from rdkit import DataStructs
    RDLogger.DisableLog('rdApp.*')
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False


class CheminformaticsProcessor:
    """Production cheminformatics processor with RDKit backend."""

    def __init__(self, fingerprint_radius: int = 2, n_bits: int = 1024):
        self.radius = fingerprint_radius
        self.n_bits = n_bits

    @property
    def is_available(self) -> bool:
        return RDKIT_AVAILABLE

    def validate_and_canonicalize(self, smiles: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates SMILES and returns (is_valid, canonical_smiles, error_message).
        """
        if not RDKIT_AVAILABLE:
            return False, None, "RDKit is not installed in the environment."

        if not smiles or not isinstance(smiles, str) or not smiles.strip():
            return False, None, "Empty or non-string SMILES string provided."

        try:
            mol = Chem.MolFromSmiles(smiles.strip())
            if mol is None:
                return False, None, f"Invalid chemical structure: cannot parse SMILES '{smiles}'."
            canonical = Chem.MolToSmiles(mol, isomericSmiles=True, canonical=True)
            return True, canonical, None
        except Exception as e:
            return False, None, f"Parsing exception: {str(e)}"

    def calculate_descriptors(self, smiles: str) -> Dict[str, Any]:
        """Calculates physicochemical descriptors for a valid SMILES string."""
        if not RDKIT_AVAILABLE:
            raise RuntimeError("RDKit is required for descriptor calculation.")

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Cannot parse SMILES: {smiles}")

        return {
            "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
            "mw": round(Descriptors.MolWt(mol), 2),
            "logp": round(Descriptors.MolLogP(mol), 2),
            "tpsa": round(Descriptors.TPSA(mol), 2),
            "hbd": Descriptors.NumHDonors(mol),
            "hba": Descriptors.NumHAcceptors(mol),
            "rotatable_bonds": Descriptors.NumRotatableBonds(mol),
            "ring_count": Descriptors.RingCount(mol),
        }

    def get_murcko_scaffold(self, smiles: str) -> Tuple[str, str]:
        """
        Extracts Bemis-Murcko generic framework / scaffold.
        Returns (scaffold_smiles, scaffold_hash_id).
        """
        if not RDKIT_AVAILABLE:
            return "UNKNOWN", "SCAFF-UNK"

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "INVALID", "SCAFF-INV"

        try:
            core = MurckoScaffold.GetScaffoldForMol(mol)
            scaff_smiles = Chem.MolToSmiles(core, isomericSmiles=False)
            if not scaff_smiles:
                # Acyclic molecules have no ring scaffold
                scaff_smiles = "Acyclic"
            scaff_id = f"SCAF-{abs(hash(scaff_smiles)) % 100000:05d}"
            return scaff_smiles, scaff_id
        except Exception:
            return "Acyclic", "SCAF-ACYCLIC"

    def compute_fingerprint(self, smiles: str) -> np.ndarray:
        """Computes Morgan ECFP4 binary fingerprint as numpy array."""
        if not RDKIT_AVAILABLE:
            raise RuntimeError("RDKit required.")

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            raise ValueError(f"Invalid SMILES: {smiles}")

        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=self.radius, nBits=self.n_bits)
        arr = np.zeros((self.n_bits,), dtype=np.int8)
        DataStructs.ConvertToNumpyArray(fp, arr)
        return arr

    def compute_fingerprints_batch(self, smiles_list: List[str]) -> np.ndarray:
        """Vectorized fingerprint calculation for candidate list."""
        fps = [self.compute_fingerprint(s) for s in smiles_list]
        return np.vstack(fps)

    def compute_pairwise_tanimoto(self, smiles_list: List[str]) -> np.ndarray:
        """Computes N x N pairwise Tanimoto similarity matrix."""
        n = len(smiles_list)
        matrix = np.eye(n, dtype=np.float32)

        mols = [Chem.MolFromSmiles(s) for s in smiles_list]
        fps = [AllChem.GetMorganFingerprintAsBitVect(m, radius=self.radius, nBits=self.n_bits) if m else None for m in mols]

        for i in range(n):
            if fps[i] is None:
                continue
            for j in range(i + 1, n):
                if fps[j] is None:
                    continue
                sim = DataStructs.TanimotoSimilarity(fps[i], fps[j])
                matrix[i, j] = sim
                matrix[j, i] = sim

        return matrix

    def compute_chemical_space_2d(self, smiles_list: List[str]) -> List[Tuple[float, float]]:
        """
        Projects molecules into 2D chemical space using PCA on Morgan fingerprints.
        Returns list of (x, y) coordinates for dashboard visualization.
        """
        if len(smiles_list) == 0:
            return []
        if len(smiles_list) == 1:
            return [(0.0, 0.0)]

        fps = self.compute_fingerprints_batch(smiles_list)
        pca = PCA(n_components=2, random_state=42)
        coords = pca.fit_transform(fps)

        # Normalize coordinates into [-10, 10] range for consistent charting
        max_val = np.max(np.abs(coords)) if np.max(np.abs(coords)) > 0 else 1.0
        norm_coords = (coords / max_val) * 10.0
        return [(round(float(c[0]), 3), round(float(c[1]), 3)) for c in norm_coords]

    def compute_novelty_scores(self, candidate_smiles: List[str], historical_smiles: List[str]) -> List[float]:
        """
        Computes novelty for each candidate relative to historical reference set:
        Novelty_i = 1.0 - max_j Tanimoto(FP_candidate_i, FP_historical_j)
        """
        if not historical_smiles:
            return [1.0 for _ in candidate_smiles]

        cand_mols = [Chem.MolFromSmiles(s) for s in candidate_smiles]
        hist_mols = [Chem.MolFromSmiles(s) for s in historical_smiles]

        cand_fps = [AllChem.GetMorganFingerprintAsBitVect(m, radius=self.radius, nBits=self.n_bits) if m else None for m in cand_mols]
        hist_fps = [AllChem.GetMorganFingerprintAsBitVect(m, radius=self.radius, nBits=self.n_bits) if m else None for m in hist_mols if m]

        novelty_scores = []
        for c_fp in cand_fps:
            if c_fp is None or not hist_fps:
                novelty_scores.append(0.5)
                continue
            max_sim = 0.0
            for h_fp in hist_fps:
                sim = DataStructs.TanimotoSimilarity(c_fp, h_fp)
                if sim > max_sim:
                    max_sim = sim
            novelty_scores.append(round(1.0 - max_sim, 4))

        return novelty_scores


chemistry_processor = CheminformaticsProcessor()
