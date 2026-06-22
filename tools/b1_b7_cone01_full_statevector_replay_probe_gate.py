#!/usr/bin/env python3
"""Full-statevector replay probe for the B1/B7 cone_01 QASM2 candidate.

T-B1-004av emitted the first full-source QASM2 candidate for the line-268 plus
line-1381 non-overlap patch subset. This gate checks whether the source and
candidate circuits produce the same 19-qubit state from the benchmark default
input after final measurements are removed.

This is deliberately a replay probe, not a symbolic unitary-equivalence proof:
it validates the concrete benchmark input state and measured-output marginal,
but it does not prove equivalence for arbitrary input states and does not move
any B7 resource ledger numbers.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_QASM_PATH = (
    ROOT / "results" / "b1_native_t_resource_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm"
)
CANDIDATE_REWRITE_PATH = ROOT / "results" / "B1_B7_cone01_qasm2_candidate_rewrite_gate_v0.json"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_full_statevector_replay_probe_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_full_statevector_replay_probe_gate.md"

METHOD = "b1_b7_cone01_full_statevector_replay_probe_gate_v0"
STATUS = "cone01_default_input_statevector_replay_probe_passed_not_symbolic_certificate"
MODEL_STATUS = "qasm2_candidate_matches_source_default_input_statevector_without_b7_credit"
FIDELITY_TOLERANCE = 1e-10
AMPLITUDE_TOLERANCE = 1e-10
PROBABILITY_TOLERANCE = 1e-10
MEASURED_QUBIT = 4


def load_circuit(path: Path) -> QuantumCircuit:
    return QuantumCircuit.from_qasm_file(str(path))


def without_final_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    return circuit.remove_final_measurements(inplace=False)


def align_global_phase(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    inner = np.vdot(reference, candidate)
    if abs(inner) == 0:
        return candidate
    return candidate * np.conj(inner / abs(inner))


def measured_marginal(statevector: Statevector, qubit: int) -> dict[str, float]:
    probabilities = statevector.probabilities([qubit])
    return {"0": float(probabilities[0]), "1": float(probabilities[1])}


def max_distribution_delta(left: dict[str, float], right: dict[str, float]) -> float:
    return max(abs(left.get(key, 0.0) - right.get(key, 0.0)) for key in set(left) | set(right))


def run_probe() -> dict[str, Any]:
    candidate_payload = load_json(CANDIDATE_REWRITE_PATH)
    candidate_qasm = ROOT / candidate_payload["summary"]["qasm2_candidate_path"]
    source_circuit = load_circuit(SOURCE_QASM_PATH)
    candidate_circuit = load_circuit(candidate_qasm)
    source_unitary_part = without_final_measurements(source_circuit)
    candidate_unitary_part = without_final_measurements(candidate_circuit)

    source_state = Statevector.from_instruction(source_unitary_part)
    candidate_state = Statevector.from_instruction(candidate_unitary_part)
    source_data = np.asarray(source_state.data)
    candidate_data = np.asarray(candidate_state.data)
    aligned_candidate = align_global_phase(source_data, candidate_data)
    amplitude_delta = np.abs(source_data - aligned_candidate)
    probability_delta = np.abs(np.abs(source_data) ** 2 - np.abs(candidate_data) ** 2)
    fidelity = float(state_fidelity(source_state, candidate_state))
    source_marginal = measured_marginal(source_state, MEASURED_QUBIT)
    candidate_marginal = measured_marginal(candidate_state, MEASURED_QUBIT)
    measured_delta = max_distribution_delta(source_marginal, candidate_marginal)
    statevector_dimension = len(source_state.data)
    accepted_removed = 0
    probe_passed = (
        1.0 - fidelity <= FIDELITY_TOLERANCE
        and float(np.max(amplitude_delta)) <= AMPLITUDE_TOLERANCE
        and float(np.max(probability_delta)) <= PROBABILITY_TOLERANCE
        and measured_delta <= PROBABILITY_TOLERANCE
    )
    summary = {
        "source_qasm": display_path(SOURCE_QASM_PATH),
        "candidate_qasm": display_path(candidate_qasm),
        "source_method": candidate_payload.get("method"),
        "qubit_count": source_circuit.num_qubits,
        "statevector_dimension": statevector_dimension,
        "source_operation_count_without_measurements": int(source_unitary_part.size()),
        "candidate_operation_count_without_measurements": int(candidate_unitary_part.size()),
        "source_cnot_count": int(source_unitary_part.count_ops().get("cx", 0)),
        "candidate_cnot_count": int(candidate_unitary_part.count_ops().get("cx", 0)),
        "candidate_cnot_delta": int(source_unitary_part.count_ops().get("cx", 0))
        - int(candidate_unitary_part.count_ops().get("cx", 0)),
        "final_measurement_removed_for_statevector": True,
        "measured_qubit": MEASURED_QUBIT,
        "source_measured_marginal": source_marginal,
        "candidate_measured_marginal": candidate_marginal,
        "measured_marginal_max_delta": measured_delta,
        "state_fidelity": fidelity,
        "infidelity": float(max(0.0, 1.0 - fidelity)),
        "max_global_phase_aligned_amplitude_delta": float(np.max(amplitude_delta)),
        "l2_global_phase_aligned_amplitude_delta": float(np.linalg.norm(source_data - aligned_candidate)),
        "max_probability_delta": float(np.max(probability_delta)),
        "statevector_replay_probe_passed": probe_passed,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_candidate_rewrite_result": display_path(CANDIDATE_REWRITE_PATH),
        "summary": summary,
        "claim_boundary": {
            "supported_claim": (
                "The T-B1-004av QASM2 candidate matches the source circuit on the "
                "benchmark default-input 19-qubit statevector after final measurements are removed."
            ),
            "unsupported_claims": [
                "This is not a symbolic unitary-equivalence proof for arbitrary input states.",
                "This is not an accepted B7 occurrence-removing certificate.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.",
            ],
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def close(left: float, right: float, tolerance: float) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=tolerance)


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "qubit_count": 19,
        "statevector_dimension": 524288,
        "source_cnot_count": 795,
        "candidate_cnot_count": 789,
        "candidate_cnot_delta": 6,
        "final_measurement_removed_for_statevector": True,
        "measured_qubit": 4,
        "statevector_replay_probe_passed": True,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field}_expected_{value}_got_{summary.get(field)}")
    if 1.0 - float(summary.get("state_fidelity", 0.0)) > FIDELITY_TOLERANCE:
        errors.append("state_fidelity_below_tolerance")
    if float(summary.get("max_global_phase_aligned_amplitude_delta", 1.0)) > AMPLITUDE_TOLERANCE:
        errors.append("max_amplitude_delta_above_tolerance")
    if float(summary.get("max_probability_delta", 1.0)) > PROBABILITY_TOLERANCE:
        errors.append("max_probability_delta_above_tolerance")
    if float(summary.get("measured_marginal_max_delta", 1.0)) > PROBABILITY_TOLERANCE:
        errors.append("measured_marginal_delta_above_tolerance")
    source_marginal = summary.get("source_measured_marginal", {})
    candidate_marginal = summary.get("candidate_measured_marginal", {})
    for bit in ["0", "1"]:
        if not close(source_marginal.get(bit, 1.0), candidate_marginal.get(bit, 0.0), PROBABILITY_TOLERANCE):
            errors.append(f"measured_marginal_{bit}_mismatch")
    for field in [
        "symbolic_unitary_equivalence_claimed",
        "arbitrary_input_equivalence_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False or payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"{field}_must_remain_false")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Full-Statevector Replay Probe Gate",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source QASM: `{summary['source_qasm']}`",
        f"- Candidate QASM: `{summary['candidate_qasm']}`",
        f"- Qubits / statevector dimension: `{summary['qubit_count']}` / `{summary['statevector_dimension']}`",
        f"- Source / candidate operations without measurements: `{summary['source_operation_count_without_measurements']}` / `{summary['candidate_operation_count_without_measurements']}`",
        f"- Source / candidate CNOT count / delta: `{summary['source_cnot_count']}` / `{summary['candidate_cnot_count']}` / `{summary['candidate_cnot_delta']}`",
        f"- State fidelity / infidelity: `{summary['state_fidelity']}` / `{summary['infidelity']}`",
        f"- Max global-phase-aligned amplitude delta: `{summary['max_global_phase_aligned_amplitude_delta']}`",
        f"- Max probability delta: `{summary['max_probability_delta']}`",
        f"- Measured q[{summary['measured_qubit']}] marginal delta: `{summary['measured_marginal_max_delta']}`",
        f"- Replay probe passed: `{summary['statevector_replay_probe_passed']}`",
        f"- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_qasm_patch_count']}` / `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"]["supported_claim"],
        "",
        "Unsupported claims:",
        "",
    ]
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "This is a stronger replay pressure gate than the structural QASM2 candidate "
                "emission: the candidate matches the source on the concrete benchmark initial "
                "state to numerical precision. It is still not a symbolic proof for arbitrary "
                "inputs and still cannot enter the B7 resource ledger until occurrence and "
                "local-U3 pricing obligations are satisfied."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    args = parser.parse_args()
    payload = run_probe()
    write_json(args.json_output, payload, True)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
