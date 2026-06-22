#!/usr/bin/env python3
"""Finite linear-span certificate for the B1/B7 cone_01 OpenQASM 3 artifact.

T-B1-004ca fixes one global phase anchor and replays selected basis anchors
and coherent pair superpositions through the project-local OpenQASM 3 parser.
This gate turns the basis-anchor part into a restricted linear-subspace
certificate: it computes the error operator on the six tested basis inputs and
reports the spectral norm for every normalized vector in that six-dimensional
span.

This remains a project-local finite-subspace certificate. It is not Qiskit
loader replay, symbolic full-space unitary equivalence, local-U3 pricing,
occurrence removal, or B7 resource credit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)
from b1_b7_cone01_openqasm3_global_phase_subspace_replay_gate import (
    SOURCE_QASM_PATH,
    anchor_suite,
    phase_from_overlap,
    without_final_measurements,
)
from b1_b7_cone01_openqasm3_local_semantic_replay_gate import (
    load_openqasm3_local_circuit,
    load_source_circuit,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_OPENQASM3_SUBSPACE_REPLAY = (
    ROOT / "results" / "B1_B7_cone01_openqasm3_global_phase_subspace_replay_gate_v0.json"
)
JSON_OUT = (
    ROOT / "results" / "B1_B7_cone01_openqasm3_linear_span_replay_certificate_gate_v0.json"
)
MD_OUT = (
    ROOT / "research" / "B1_B7_cone01_openqasm3_linear_span_replay_certificate_gate.md"
)

METHOD = "b1_b7_cone01_openqasm3_linear_span_replay_certificate_gate_v0"
STATUS = "cone01_openqasm3_linear_span_replay_certificate_passed_not_full_unitary"
MODEL_STATUS = (
    "project_local_openqasm3_candidate_has_six_dimensional_linear_span_certificate_without_b7_credit"
)
SPECTRAL_NORM_TOLERANCE = 1e-10
GRAM_TOLERANCE = 1e-10
AMPLITUDE_TOLERANCE = 1e-10
PROBABILITY_TOLERANCE = 1e-10


def error_operator_metrics(
    source_circuit: Any,
    openqasm3_circuit: Any,
    global_phase_anchor: complex,
) -> dict[str, Any]:
    anchors = anchor_suite(source_circuit.num_qubits)
    source_columns: list[np.ndarray] = []
    candidate_columns: list[np.ndarray] = []
    basis_rows: list[dict[str, Any]] = []
    for label, state in anchors:
        source_state = state.evolve(source_circuit)
        candidate_state = state.evolve(openqasm3_circuit)
        source_data = np.asarray(source_state.data)
        anchored_candidate = np.asarray(candidate_state.data) * np.conj(global_phase_anchor)
        error = source_data - anchored_candidate
        source_columns.append(source_data)
        candidate_columns.append(anchored_candidate)
        basis_rows.append(
            {
                "label": label,
                "l2_error": float(np.linalg.norm(error)),
                "max_amplitude_delta": float(np.max(np.abs(error))),
                "max_probability_delta": float(
                    np.max(np.abs(np.abs(source_data) ** 2 - np.abs(candidate_state.data) ** 2))
                ),
            }
        )

    source_matrix = np.column_stack(source_columns)
    candidate_matrix = np.column_stack(candidate_columns)
    error_matrix = source_matrix - candidate_matrix
    error_gram = error_matrix.conj().T @ error_matrix
    error_eigenvalues = np.linalg.eigvalsh(error_gram)
    spectral_norm = float(np.sqrt(max(0.0, float(np.max(error_eigenvalues)))))
    source_gram = source_matrix.conj().T @ source_matrix
    candidate_gram = candidate_matrix.conj().T @ candidate_matrix
    gram_delta = np.abs(source_gram - candidate_gram)
    cross_gram_delta = np.abs(source_matrix.conj().T @ candidate_matrix - np.eye(len(anchors)))
    return {
        "basis_anchor_labels": [label for label, _ in anchors],
        "basis_anchor_case_count": len(anchors),
        "basis_anchor_rows": basis_rows,
        "linear_span_dimension": len(anchors),
        "linear_span_error_spectral_norm": spectral_norm,
        "linear_span_error_frobenius_norm": float(np.linalg.norm(error_matrix, "fro")),
        "max_basis_l2_error": max(row["l2_error"] for row in basis_rows),
        "max_basis_amplitude_delta": max(row["max_amplitude_delta"] for row in basis_rows),
        "max_basis_probability_delta": max(row["max_probability_delta"] for row in basis_rows),
        "max_source_candidate_gram_delta": float(np.max(gram_delta)),
        "max_cross_gram_delta": float(np.max(cross_gram_delta)),
    }


def build_payload() -> dict[str, Any]:
    subspace_payload = load_json(SOURCE_OPENQASM3_SUBSPACE_REPLAY)
    subspace_summary = subspace_payload.get("summary", {})
    openqasm3_path = ROOT / subspace_summary["openqasm3_candidate_path"]
    source_unitary = without_final_measurements(load_source_circuit())
    openqasm3_circuit, local_parse = load_openqasm3_local_circuit(openqasm3_path)
    openqasm3_unitary = without_final_measurements(openqasm3_circuit)
    zero_state = anchor_suite(source_unitary.num_qubits)[0][1]
    zero_source = zero_state.evolve(source_unitary)
    zero_openqasm3 = zero_state.evolve(openqasm3_unitary)
    global_phase_anchor = phase_from_overlap(
        complex(np.vdot(np.asarray(zero_source.data), np.asarray(zero_openqasm3.data)))
    )
    span_metrics = error_operator_metrics(source_unitary, openqasm3_unitary, global_phase_anchor)
    coherent_cases = [
        case
        for case in subspace_summary.get("input_cases", [])
        if case.get("input_kind") == "coherent_pair_superposition"
    ]
    coherent_witness_passed = all(case.get("passed") is True for case in coherent_cases)
    accepted_removed = 0
    full_dimension = 2 ** source_unitary.num_qubits
    finite_span_passed = (
        not local_parse["errors"]
        and subspace_summary.get("openqasm3_global_phase_subspace_replay_passed") is True
        and coherent_witness_passed
        and span_metrics["linear_span_error_spectral_norm"] <= SPECTRAL_NORM_TOLERANCE
        and span_metrics["max_source_candidate_gram_delta"] <= GRAM_TOLERANCE
        and span_metrics["max_cross_gram_delta"] <= GRAM_TOLERANCE
        and span_metrics["max_basis_amplitude_delta"] <= AMPLITUDE_TOLERANCE
        and span_metrics["max_basis_probability_delta"] <= PROBABILITY_TOLERANCE
    )
    summary = {
        "source_openqasm3_subspace_replay_method": subspace_payload.get("method"),
        "source_openqasm3_global_phase_subspace_replay_gate": display_path(
            SOURCE_OPENQASM3_SUBSPACE_REPLAY
        ),
        "source_qasm": display_path(SOURCE_QASM_PATH),
        "openqasm3_candidate_path": display_path(openqasm3_path),
        "project_local_openqasm3_parser_passed": not local_parse["errors"],
        "project_local_openqasm3_parser_error_count": len(local_parse["errors"]),
        "project_local_operation_counts": local_parse["operation_counts"],
        "qubit_count": source_unitary.num_qubits,
        "bit_count": local_parse["bit_count"],
        "statement_count": local_parse["statement_count"],
        "operation_row_count": local_parse["operation_row_count"],
        "statevector_dimension": full_dimension,
        "source_cnot_count": int(source_unitary.count_ops().get("cx", 0)),
        "openqasm3_cnot_count": int(openqasm3_unitary.count_ops().get("cx", 0)),
        "openqasm3_cnot_delta": int(source_unitary.count_ops().get("cx", 0))
        - int(openqasm3_unitary.count_ops().get("cx", 0)),
        "final_measurement_removed_for_statevector": True,
        "global_phase_anchor_label": "zero",
        "global_phase_anchor_radians": float(np.angle(global_phase_anchor)),
        "finite_openqasm3_linear_span_certificate_passed": finite_span_passed,
        "certified_input_subspace_dimension": span_metrics["linear_span_dimension"],
        "full_input_space_dimension": full_dimension,
        "certified_input_subspace_fraction": span_metrics["linear_span_dimension"] / full_dimension,
        "coherent_pair_witness_count": len(coherent_cases),
        "coherent_pair_witness_passed": coherent_witness_passed,
        **span_metrics,
        "accepted_project_local_openqasm3_linear_span_certificate_count": (
            1 if finite_span_passed else 0
        ),
        "accepted_qiskit_loader_parse_artifact_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_removed) * PROXY_T_PER_OCCURRENCE,
        ),
        "qiskit_loader_parse_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": 0,
    }
    validation_errors = validate_summary(summary, local_parse["errors"])
    summary["validation_error_count"] = len(validation_errors)
    return {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_openqasm3_global_phase_subspace_replay_gate": display_path(
            SOURCE_OPENQASM3_SUBSPACE_REPLAY
        ),
        "source_qasm": display_path(SOURCE_QASM_PATH),
        "openqasm3_candidate_qasm": display_path(openqasm3_path),
        "summary": summary,
        "project_local_parser_errors": local_parse["errors"],
        "validation_errors": validation_errors,
        "claim_boundary": {
            "supported_claim": (
                "The project-local OpenQASM 3 candidate has a tolerance-bounded "
                "replay certificate on the six-dimensional input span generated "
                "by the listed basis anchors, under the zero-input global phase anchor."
            ),
            "unsupported_claims": [
                "This is not a Qiskit OpenQASM 3 loader parse or replay artifact.",
                "This is not symbolic unitary equivalence for the full circuit.",
                "This is not arbitrary-input or full Hilbert-space coverage.",
                "This is not an accepted B7 occurrence-removing certificate.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not price or eliminate the remaining line-1381 off-grid local-U3 parameters.",
            ],
            "qiskit_loader_parse_claimed": False,
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "full_hilbert_space_certificate_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }


def validate_summary(summary: dict[str, Any], parser_errors: list[str]) -> list[str]:
    errors: list[str] = []
    expected = {
        "project_local_openqasm3_parser_passed": True,
        "project_local_openqasm3_parser_error_count": 0,
        "project_local_operation_counts": {"U": 487, "rz": 601, "cx": 789, "measure": 1},
        "qubit_count": 19,
        "bit_count": 1,
        "statement_count": 1884,
        "operation_row_count": 1878,
        "statevector_dimension": 524288,
        "source_cnot_count": 795,
        "openqasm3_cnot_count": 789,
        "openqasm3_cnot_delta": 6,
        "final_measurement_removed_for_statevector": True,
        "global_phase_anchor_label": "zero",
        "certified_input_subspace_dimension": 6,
        "full_input_space_dimension": 524288,
        "coherent_pair_witness_count": 15,
        "coherent_pair_witness_passed": True,
        "finite_openqasm3_linear_span_certificate_passed": True,
        "accepted_project_local_openqasm3_linear_span_certificate_count": 1,
        "accepted_qiskit_loader_parse_artifact_count": 0,
        "accepted_symbolic_unitary_equivalence_count": 0,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "full_hilbert_space_certificate_claimed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_local_u3_pricing_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "qiskit_loader_parse_claimed": False,
        "local_u3_pricing_accepted": False,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field}_expected_{value}_got_{summary.get(field)}")
    if parser_errors:
        errors.append("project_local_parser_errors_not_empty")
    numeric_bounds = {
        "linear_span_error_spectral_norm": SPECTRAL_NORM_TOLERANCE,
        "max_basis_l2_error": SPECTRAL_NORM_TOLERANCE,
        "max_basis_amplitude_delta": AMPLITUDE_TOLERANCE,
        "max_basis_probability_delta": PROBABILITY_TOLERANCE,
        "max_source_candidate_gram_delta": GRAM_TOLERANCE,
        "max_cross_gram_delta": GRAM_TOLERANCE,
    }
    for field, upper_bound in numeric_bounds.items():
        if float(summary.get(field, 1.0)) > upper_bound:
            errors.append(f"{field}_above_{upper_bound}")
    expected_fraction = 6 / 524288
    if abs(float(summary.get("certified_input_subspace_fraction", 0.0)) - expected_fraction) > 1e-18:
        errors.append("certified_input_subspace_fraction_mismatch")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Linear-Span Replay Certificate Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Source OpenQASM 3 subspace replay: `{payload['source_openqasm3_global_phase_subspace_replay_gate']}`",
        f"- OpenQASM 3 candidate: `{payload['openqasm3_candidate_qasm']}`",
        "",
        "## Result",
        "",
        f"- Finite OpenQASM 3 linear-span certificate passed: `{summary['finite_openqasm3_linear_span_certificate_passed']}`",
        f"- Certified input subspace dimension: `{summary['certified_input_subspace_dimension']}` of `{summary['full_input_space_dimension']}`",
        f"- Certified input subspace fraction: `{summary['certified_input_subspace_fraction']}`",
        f"- Linear-span error spectral norm: `{summary['linear_span_error_spectral_norm']}`",
        f"- Max basis L2 error: `{summary['max_basis_l2_error']}`",
        f"- Max basis amplitude delta: `{summary['max_basis_amplitude_delta']}`",
        f"- Max basis probability delta: `{summary['max_basis_probability_delta']}`",
        f"- Max source/candidate Gram delta: `{summary['max_source_candidate_gram_delta']}`",
        f"- Max cross-Gram delta: `{summary['max_cross_gram_delta']}`",
        f"- Coherent pair witnesses passed: `{summary['coherent_pair_witness_passed']}` across `{summary['coherent_pair_witness_count']}` cases",
        f"- Source / OpenQASM 3 CNOT count / delta: `{summary['source_cnot_count']}` / `{summary['openqasm3_cnot_count']}` / `{summary['openqasm3_cnot_delta']}`",
        f"- Accepted OpenQASM 3 linear-span certificates: `{summary['accepted_project_local_openqasm3_linear_span_certificate_count']}`",
        f"- Accepted Qiskit loader / symbolic equivalence / local-U3 pricing artifacts: `{summary['accepted_qiskit_loader_parse_artifact_count']}` / `{summary['accepted_symbolic_unitary_equivalence_count']}` / `{summary['accepted_local_u3_pricing_certificate_count']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
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
            payload["claim_boundary"]["supported_claim"],
            "",
            "Unsupported claims:",
            "",
        ]
    )
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(
        [
            "",
            "## Next Required Gate",
            "",
            "Move from project-local OpenQASM 3 finite-span evidence to loader-backed OpenQASM 3 replay, full-space symbolic/local-unitary evidence, or honest local-U3 pricing before any B7 resource credit is accepted.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build_payload()
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
