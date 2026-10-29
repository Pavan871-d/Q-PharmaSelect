"""
Tests for QpiAI Quantum SDK / QCloud Integration.
"""

import pytest
import numpy as np
from backend.app.services.quantum.qcloud_runner import quantum_service


def test_qpiai_sdk_installed():
    assert quantum_service.sdk_version != "NOT_INSTALLED"
    assert quantum_service.sdk_version.startswith("0.7")


def test_molecular_quantum_circuit_generation():
    features = np.array([0.5, -1.2, 2.1, 0.0], dtype=np.float32)
    num_qubits = 4

    circuit = quantum_service.build_molecular_circuit(features, num_qubits=num_qubits)
    assert circuit.num_qubits == num_qubits
    assert circuit.num_clbits == num_qubits
    assert circuit.depth() > 0

    # Verify QASM generation
    qasm = circuit.to_qasm()
    assert "OPENQASM" in qasm or "qreg" in qasm or "qubit" in qasm


def test_quantum_experiment_execution():
    np.random.seed(42)
    X_train = np.random.uniform(0, 1, (20, 128))
    y_train = np.random.uniform(4.0, 9.0, 20)
    X_test = np.random.uniform(0, 1, (10, 128))
    y_test = np.random.uniform(4.0, 9.0, 10)

    res = quantum_service.run_quantum_experiment(
        X_train_fps=X_train,
        y_train=y_train,
        X_test_fps=X_test,
        y_test=y_test,
        num_qubits=4,
        num_shots=256
    )

    assert res["status"] == "SUCCESS"
    assert res["num_qubits"] == 4
    assert res["num_shots"] == 256
    assert res["execution_time_ms"] > 0
    assert "classical_baseline_rmse" in res
    assert "quantum_hybrid_rmse" in res
    assert res["evidence_status"] in ["QPIAI QUANTUM SIMULATION (LOCAL)", "QPIAI QUANTUM EXECUTION VERIFIED"]
    assert len(res["measurement_counts_summary"]) > 0

