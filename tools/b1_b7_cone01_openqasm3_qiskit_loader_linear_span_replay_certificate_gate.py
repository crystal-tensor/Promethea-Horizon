#!/usr/bin/env python3
"""Qiskit-loader finite linear-span certificate for the B1/B7 OpenQASM 3 artifact.

This gate upgrades the project-local finite-span certificate to the Qiskit
OpenQASM 3 loader path. It fixes the zero-input global phase anchor and
computes the replay error operator on the six basis anchors used by the
subspace witness. The result is a loader-backed finite-subspace certificate,
not a symbolic full-space equivalence proof, local-U3 pricing certificate, or
B7 resource ledger improvement.
"""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, qasm3

from b1_b7_cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_gate import (
    PROJECT_LOCAL_GLOBAL_PHASE_PATH,
    QASM3_PATH,
    SOURCE_QASM_PATH,
    anchor_suite,
    phase_from_overlap,
    without_final_measurements,
)


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESEARCH = ROOT / "research"

METHOD = "b1_b7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate_v0"
STATUS = "cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_passed"
MODEL_STATUS = (
    "qiskit_loader_openqasm3_has_six_dimensional_linear_span_certificate_without_b7_credit"
)

PROJECT_LOCAL_SPAN_PATH = (
    RESULTS / "B1_B7_cone01_openqasm3_linear_span_replay_certificate_gate_v0.json"
)
QISKIT_LOADER_GLOBAL_PHASE_PATH = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_gate_v0.json"
)
OUT_JSON = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate_v0.json"
)
OUT_MD = (
    RESEARCH / "B1_B7_cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_gate.md"
)

SPECTRAL_NORM_TOLERANCE = 1e-10
GRAM_TOLERANCE = 1e-10
AMPLITUDE_TOLERANCE = 1e-10
PROBABILITY_TOLERANCE = 1e-10


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def linear_span_metrics(
    source_circuit: QuantumCircuit,
    qiskit_loader_circuit: QuantumCircuit,
    global_phase_anchor: complex,
) -> dict[str, Any]:
    anchors = anchor_suite(source_circuit.num_qubits)
    source_columns: list[np.ndarray] = []
    qiskit_columns: list[np.ndarray] = []
    basis_rows: list[dict[str, Any]] = []

    for label, state in anchors:
        source_state = state.evolve(source_circuit)
        qiskit_state = state.evolve(qiskit_loader_circuit)
        source_data = np.asarray(source_state.data)
        qiskit_data = np.asarray(qiskit_state.data)
        aligned_qiskit = qiskit_data * np.conj(global_phase_anchor)
        error = source_data - aligned_qiskit
        source_columns.append(source_data)
        qiskit_columns.append(aligned_qiskit)
        basis_rows.append(
            {
                "label": label,
                "l2_error": float(np.linalg.norm(error)),
                "max_amplitude_delta": float(np.max(np.abs(error))),
                "max_probability_delta": float(
                    np.max(np.abs(np.abs(source_data) ** 2 - np.abs(qiskit_data) ** 2))
                ),
            }
        )

    source_matrix = np.column_stack(source_columns)
    qiskit_matrix = np.column_stack(qiskit_columns)
    error_matrix = source_matrix - qiskit_matrix
    error_gram = error_matrix.conj().T @ error_matrix
    error_eigenvalues = np.linalg.eigvalsh(error_gram)
    source_gram = source_matrix.conj().T @ source_matrix
    qiskit_gram = qiskit_matrix.conj().T @ qiskit_matrix
    cross_gram = source_matrix.conj().T @ qiskit_matrix

    return {
        "basis_anchor_labels": [label for label, _ in anchors],
        "basis_anchor_case_count": len(anchors),
        "basis_anchor_rows": basis_rows,
        "linear_span_dimension": len(anchors),
        "linear_span_error_spectral_norm": float(
            np.sqrt(max(0.0, float(np.max(error_eigenvalues))))
        ),
        "linear_span_error_frobenius_norm": float(np.linalg.norm(error_matrix, "fro")),
        "max_basis_l2_error": max(row["l2_error"] for row in basis_rows),
        "max_basis_amplitude_delta": max(row["max_amplitude_delta"] for row in basis_rows),
        "max_basis_probability_delta": max(row["max_probability_delta"] for row in basis_rows),
        "max_source_candidate_gram_delta": float(np.max(np.abs(source_gram - qiskit_gram))),
        "max_cross_gram_delta": float(np.max(np.abs(cross_gram - np.eye(len(anchors))))),
    }


def build_payload() -> dict[str, Any]:
    project_local_span = load_json(PROJECT_LOCAL_SPAN_PATH)
    qiskit_global_phase = load_json(QISKIT_LOADER_GLOBAL_PHASE_PATH)
    project_local_global_phase = load_json(PROJECT_LOCAL_GLOBAL_PHASE_PATH)

    source_circuit = QuantumCircuit.from_qasm_file(str(SOURCE_QASM_PATH))
    qiskit_circuit = qasm3.loads(QASM3_PATH.read_text(encoding="utf-8"))
    source_unitary = without_final_measurements(source_circuit)
    qiskit_unitary = without_final_measurements(qiskit_circuit)

    errors: list[str] = []
    if (
        project_local_span.get("status")
        != "cone01_openqasm3_linear_span_replay_certificate_passed_not_full_unitary"
    ):
        errors.append("source project-local linear-span certificate status changed")
    if (
        qiskit_global_phase.get("status")
        != "cone01_openqasm3_qiskit_loader_global_phase_subspace_replay_passed"
    ):
        errors.append("source Qiskit-loader global-phase replay status changed")
    if (
        project_local_global_phase.get("status")
        != "cone01_openqasm3_global_phase_subspace_replay_passed_not_symbolic_certificate"
    ):
        errors.append("source project-local global-phase replay status changed")

    anchors = anchor_suite(source_unitary.num_qubits)
    zero_source = anchors[0][1].evolve(source_unitary)
    zero_qiskit = anchors[0][1].evolve(qiskit_unitary)
    global_phase_anchor = phase_from_overlap(
        complex(np.vdot(np.asarray(zero_source.data), np.asarray(zero_qiskit.data)))
    )
    span_metrics = linear_span_metrics(source_unitary, qiskit_unitary, global_phase_anchor)

    qiskit_counts = {key: int(value) for key, value in qiskit_circuit.count_ops().items()}
    expected_counts = {"cx": 789, "rz": 601, "u": 487, "measure": 1}
    if qiskit_counts != expected_counts:
        errors.append("Qiskit-loader operation counts changed")
    if qiskit_circuit.num_qubits != 19:
        errors.append("Qiskit-loader qubit count changed")
    if qiskit_circuit.num_clbits != 1:
        errors.append("Qiskit-loader clbit count changed")
    if qiskit_circuit.depth() != 1483:
        errors.append("Qiskit-loader depth changed")

    finite_span_passed = (
        span_metrics["linear_span_error_spectral_norm"] <= SPECTRAL_NORM_TOLERANCE
        and span_metrics["max_source_candidate_gram_delta"] <= GRAM_TOLERANCE
        and span_metrics["max_cross_gram_delta"] <= GRAM_TOLERANCE
        and span_metrics["max_basis_amplitude_delta"] <= AMPLITUDE_TOLERANCE
        and span_metrics["max_basis_probability_delta"] <= PROBABILITY_TOLERANCE
    )
    if not finite_span_passed:
        errors.append("Qiskit-loader finite linear-span certificate exceeded tolerance")

    full_dimension = 2 ** source_unitary.num_qubits
    summary = {
        "source_project_local_linear_span_certificate_gate": rel(PROJECT_LOCAL_SPAN_PATH),
        "source_qiskit_loader_global_phase_subspace_gate": rel(QISKIT_LOADER_GLOBAL_PHASE_PATH),
        "source_project_local_global_phase_subspace_gate": rel(PROJECT_LOCAL_GLOBAL_PHASE_PATH),
        "source_qasm_path": rel(SOURCE_QASM_PATH),
        "openqasm3_candidate_path": rel(QASM3_PATH),
        "qiskit_version": package_version("qiskit"),
        "qiskit_qasm3_import_version": package_version("qiskit-qasm3-import"),
        "openqasm3_package_version": package_version("openqasm3"),
        "qiskit_loader_passed": True,
        "qiskit_num_qubits": int(qiskit_circuit.num_qubits),
        "qiskit_num_clbits": int(qiskit_circuit.num_clbits),
        "qiskit_depth": int(qiskit_circuit.depth()),
        "qiskit_count_ops": qiskit_counts,
        "expected_qiskit_count_ops": expected_counts,
        "statevector_dimension": full_dimension,
        "source_operation_count_without_measurements": int(source_unitary.size()),
        "qiskit_operation_count_without_measurements": int(qiskit_unitary.size()),
        "source_cnot_count": int(source_unitary.count_ops().get("cx", 0)),
        "qiskit_cnot_count": int(qiskit_unitary.count_ops().get("cx", 0)),
        "qiskit_cnot_delta": int(source_unitary.count_ops().get("cx", 0))
        - int(qiskit_unitary.count_ops().get("cx", 0)),
        "final_measurement_removed_for_statevector": True,
        "global_phase_anchor_label": "zero",
        "global_phase_anchor_radians": float(np.angle(global_phase_anchor)),
        "qiskit_loader_linear_span_certificate_passed": finite_span_passed,
        "certified_input_subspace_dimension": span_metrics["linear_span_dimension"],
        "full_input_space_dimension": full_dimension,
        "certified_input_subspace_fraction": span_metrics["linear_span_dimension"] / full_dimension,
        **span_metrics,
        "accepted_qiskit_loader_parse_artifact_count": 1,
        "accepted_qiskit_loader_replay_artifact_count": 1,
        "accepted_qiskit_loader_global_phase_subspace_replay_artifact_count": 1,
        "accepted_qiskit_loader_linear_span_certificate_count": 1 if finite_span_passed else 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "qiskit_loader_parse_claimed": True,
        "qiskit_loader_replay_claimed": True,
        "qiskit_loader_global_phase_subspace_replay_claimed": True,
        "qiskit_loader_linear_span_certificate_claimed": finite_span_passed,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(errors),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if not errors else "cone01_openqasm3_qiskit_loader_linear_span_replay_certificate_failed",
        "model_status": MODEL_STATUS if not errors else "qiskit_loader_openqasm3_linear_span_certificate_rejected",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "claim_boundary": {
            "supported_claim": (
                "The Qiskit-loaded OpenQASM 3 candidate has a tolerance-bounded "
                "six-dimensional finite linear-span replay certificate under the "
                "zero-input global phase anchor."
            ),
            "qiskit_loader_parse_claimed": True,
            "qiskit_loader_replay_claimed": True,
            "qiskit_loader_global_phase_subspace_replay_claimed": True,
            "qiskit_loader_linear_span_certificate_claimed": finite_span_passed,
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "full_hilbert_space_certificate_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This is a six-dimensional finite-subspace certificate, not full-space equivalence.",
                "This is not a symbolic exact full-circuit unitary proof.",
                "This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not improve the B7 resource ledger.",
            ],
        },
        "summary": summary,
        "validation_errors": errors,
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Linear-Span Replay Certificate Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Supported claim: {claims['supported_claim']}",
        "",
        "## Inputs",
        "",
        f"- Project-local linear-span gate: `{summary['source_project_local_linear_span_certificate_gate']}`",
        f"- Qiskit-loader global-phase gate: `{summary['source_qiskit_loader_global_phase_subspace_gate']}`",
        f"- OpenQASM 3 candidate: `{summary['openqasm3_candidate_path']}`",
        "",
        "## Loader Evidence",
        "",
        f"- Qiskit / qiskit-qasm3-import / openqasm3 versions: {summary['qiskit_version']} / {summary['qiskit_qasm3_import_version']} / {summary['openqasm3_package_version']}",
        f"- Qubits / clbits / depth: {summary['qiskit_num_qubits']} / {summary['qiskit_num_clbits']} / {summary['qiskit_depth']}",
        f"- Operation counts: {summary['qiskit_count_ops']}",
        "",
        "## Linear-Span Certificate",
        "",
        f"- Global phase anchor: `{summary['global_phase_anchor_label']}` / `{summary['global_phase_anchor_radians']}` radians",
        f"- Certified input subspace dimension: {summary['certified_input_subspace_dimension']} of {summary['full_input_space_dimension']}",
        f"- Certified input subspace fraction: {summary['certified_input_subspace_fraction']}",
        f"- Linear-span spectral / Frobenius error: {summary['linear_span_error_spectral_norm']} / {summary['linear_span_error_frobenius_norm']}",
        f"- Max basis L2 / amplitude / probability delta: {summary['max_basis_l2_error']} / {summary['max_basis_amplitude_delta']} / {summary['max_basis_probability_delta']}",
        f"- Max source-candidate Gram / cross-Gram delta: {summary['max_source_candidate_gram_delta']} / {summary['max_cross_gram_delta']}",
        f"- Source / Qiskit CNOT count / delta: {summary['source_cnot_count']} / {summary['qiskit_cnot_count']} / {summary['qiskit_cnot_delta']}",
        f"- Accepted Qiskit-loader parse / replay / global-anchor / linear-span artifacts: {summary['accepted_qiskit_loader_parse_artifact_count']} / {summary['accepted_qiskit_loader_replay_artifact_count']} / {summary['accepted_qiskit_loader_global_phase_subspace_replay_artifact_count']} / {summary['accepted_qiskit_loader_linear_span_certificate_count']}",
        f"- Accepted occurrence / proxy-T reduction / B7 claim: {summary['accepted_occurrence_removal']} / {summary['accepted_proxy_t_reduction']} / {summary['b7_ledger_improvement_claimed']}",
        "",
        "## Basis Rows",
        "",
        "| Basis anchor | L2 error | Max amplitude delta | Max probability delta |",
        "|---|---:|---:|---:|",
    ]
    for row in summary["basis_anchor_rows"]:
        lines.append(
            f"| `{row['label']}` | `{row['l2_error']}` | `{row['max_amplitude_delta']}` | `{row['max_probability_delta']}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            *[f"- {claim}" for claim in claims["unsupported_claims"]],
            "",
            "## Validation",
            "",
            f"- Qiskit-loader linear-span certificate passed: {summary['qiskit_loader_linear_span_certificate_passed']}",
            f"- Validation errors: {summary['validation_error_count']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if payload["validation_errors"]:
        raise SystemExit(
            "OpenQASM3 Qiskit-loader linear-span certificate failed: "
            + "; ".join(payload["validation_errors"])
        )


if __name__ == "__main__":
    main()
