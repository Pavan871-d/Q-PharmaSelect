"""
Integration Tests for Q-PharmaSelect FastAPI Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["app"] == "Q-PharmaSelect"


def test_data_summary_endpoint():
    response = client.get("/api/data/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_compounds"] >= 80
    assert data["total_scaffolds"] > 10
    assert "evidence_breakdown" in data


def test_compounds_list_endpoint():
    response = client.get("/api/data/compounds?limit=10")
    assert response.status_code == 200
    compounds = response.json()
    assert len(compounds) == 10
    first = compounds[0]
    assert "canonical_smiles" in first
    assert "compound_id" in first
    assert "cost" in first


def test_model_training_endpoint():
    payload = {
        "target_id": "CHEMBL203",
        "assay_id": "CHEMBL615112",
        "model_type": "random_forest",
        "split_method": "scaffold_split",
        "test_size": 0.25,
        "random_seed": 42
    }
    response = client.post("/api/models/train", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["r2"] is not None
    assert data["rmse"] > 0
    assert data["num_train"] > 0
    assert data["num_test"] > 0


def test_quantum_run_endpoint():
    payload = {
        "target_id": "CHEMBL203",
        "backend_name": "QpiAI-QSV-Simulator",
        "num_qubits": 4,
        "num_shots": 256
    }
    response = client.post("/api/quantum/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["num_qubits"] == 4
    assert "classical_baseline_rmse" in data
    assert "quantum_hybrid_rmse" in data


def test_optimization_run_endpoint():
    payload = {
        "target_id": "CHEMBL203",
        "batch_size": 10,
        "total_budget": 7000.0,
        "weight_activity": 1.0,
        "weight_exploration": 0.5,
        "weight_novelty": 0.8,
        "weight_diversity": 0.7,
        "weight_cost": 0.3,
        "unknown_availability_policy": "EXCLUDE"
    }
    response = client.post("/api/optimization/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["batch_size_satisfied"] is True
    assert data["budget_satisfied"] is True
    assert data["selected_count"] == 10
    assert len(data["selected_compounds"]) == 10


def test_retrospective_validation_endpoint():
    response = client.post("/api/validation/run")
    assert response.status_code == 200
    data = response.json()
    assert data["selected_batch_enrichment_factor"] > 0
    assert data["selected_batch_observed_hits"] >= 0
    assert len(data["baselines"]) >= 3


def test_report_export_endpoint():
    response = client.get("/api/reports/export/selected-csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "rank,compound_id" in response.text


def test_integrations_status_endpoint():
    response = client.get("/api/integrations/status")
    assert response.status_code == 200
    data = response.json()
    assert "qcloud" in data
    assert "qpiai_opt" in data
    assert "python_packages" in data["runtime_environment"]

