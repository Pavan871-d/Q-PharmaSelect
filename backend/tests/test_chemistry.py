"""
Tests for Cheminformatics Processing Engine.
"""

import pytest
import numpy as np
from backend.app.services.chemistry.processor import chemistry_processor


def test_valid_smiles_canonicalization():
    is_valid, canon, err = chemistry_processor.validate_and_canonicalize("C1=CC=CC=C1")
    assert is_valid is True
    assert canon == "c1ccccc1"
    assert err is None


def test_invalid_smiles_rejection():
    is_valid, canon, err = chemistry_processor.validate_and_canonicalize("INVALID_NOT_A_SMILES")
    assert is_valid is False
    assert canon is None
    assert "Invalid chemical structure" in err


def test_molecular_descriptors():
    # Erlotinib SMILES
    erlotinib = "COc1cc2c(ncnc2cc1OC)Nc3cccc(c3)C#C"
    desc = chemistry_processor.calculate_descriptors(erlotinib)
    assert desc["mw"] > 300.0
    assert desc["logp"] > 2.0
    assert desc["hbd"] >= 1
    assert desc["hba"] >= 4
    assert desc["rotatable_bonds"] >= 4


def test_bemis_murcko_scaffold():
    gefitinib = "COc1cc2c(ncnc2cc1OCCCN3CCOCC3)Nc4ccc(c(c4)Cl)F"
    scaff_smiles, scaff_id = chemistry_processor.get_murcko_scaffold(gefitinib)
    assert scaff_smiles != "Acyclic"
    assert scaff_id.startswith("SCAF-")


def test_tanimoto_similarity_matrix():
    smiles = [
        "c1ccccc1",  # Benzene
        "c1ccncc1",  # Pyridine
        "COc1cc2c(ncnc2cc1OC)Nc3cccc(c3)C#C"  # Erlotinib
    ]
    mat = chemistry_processor.compute_pairwise_tanimoto(smiles)
    assert mat.shape == (3, 3)
    # Self-similarity must be 1.0
    assert np.allclose(np.diag(mat), 1.0)
    # Symmetry
    assert np.allclose(mat, mat.T)
    # Different molecules have similarity in [0, 1)
    assert 0.0 <= mat[0, 1] < 1.0


def test_chemical_space_2d_projection():
    smiles = [
        "COc1cc2c(ncnc2cc1OC)Nc3cccc(c3)C#C",
        "COc1cc2c(ncnc2cc1OCCCN3CCOCC3)Nc4ccc(c(c4)Cl)F",
        "CS(=O)(=O)CCNCc1ccc(o1)c2ccc3c(c2)c(c4cc(c(cc4)Cl)OCc5cccc(c5)F)ncn3"
    ]
    coords = chemistry_processor.compute_chemical_space_2d(smiles)
    assert len(coords) == 3
    for cx, cy in coords:
        assert isinstance(cx, float)
        assert isinstance(cy, float)

