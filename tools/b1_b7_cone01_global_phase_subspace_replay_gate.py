#!/usr/bin/env python3
"""Global-phase-anchored subspace replay gate for the B1/B7 cone_01 candidate.

T-B1-004ay checks phase spread across sampled inputs, but still reports each
case as an independent replay observation. This gate fixes one global phase
from the zero input and then reuses that same phase for a small computational
basis subspace and coherent pair superpositions.

This is a stricter sampled subspace replay check. It is not a symbolic
unitary-equivalence proof, not an exhaustive input-space certificate, and not
accepted B7 resource credit.
"""

from __future__ import annotations

import argparse
import json
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
JSON_OUT = ROOT / "results" / "B1_B7_cone01_global_phase_subspace_replay_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_global_phase_subspace_replay_gate.md"

METHOD = "b1_b7_cone01_global_phase_subspace_replay_gate_v0"
STATUS = "cone01_global_phase_subspace_replay_passed_not_symbolic_certificate"
MODEL_STATUS = "qasm2_candidate_has_global_phase_anchored_subspace_replay_without_b7_credit"
PHASE_TOLERANCE = 1e-10
FIDELITY_TOLERANCE = 1e-10
AMPLITUDE_TOLERANCE = 1e-10
PROBABILITY_TOLERANCE = 1e-10


def load_circuit(path: Path) -> QuantumCircuit:
    return QuantumCircuit.from_qasm_file(str(path))


def without_final_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    return circuit.remove_final_measurements(inplace=False)


def basis_state(num_qubits: int, active_qubits: tuple[int, ...]) -> Statevector:
    prep = QuantumCircuit(num_qubits)
    for qubit in active_qubits:
        prep.x(qubit)
    return Statevector.from_instruction(prep)


def normalized_superposition(left: Statevector, right: Statevector, phase: complex) -> Statevector:
    vector = np.asarray(left.data) + phase * np.asarray(right.data)
    return Statevector(vector / np.linalg.norm(vector))


def anchor_suite(num_qubits: int) -> list[tuple[str, Statevector]]:
    return [
        ("zero", basis_state(num_qubits, ())),
        ("x_q0", basis_state(num_qubits, (0,))),
        ("x_q4", basis_state(num_qubits, (4,))),
        ("x_q14", basis_state(num_qubits, (14,))),
        ("x_q0_q4", basis_state(num_qubits, (0, 4))),
        ("x_q4_q14", basis_state(num_qubits, (4, 14))),
    ]


def superposition_suite(anchors: list[tuple[str, Statevector]]) -> list[tuple[str, Statevector]]:
    by_label = dict(anchors)
    pairs = [
        ("zero", "x_q0"),
        ("zero", "x_q4"),
        ("x_q0", "x_q14"),
        ("x_q4", "x_q0_q4"),
        ("x_q0_q4", "x_q4_q14"),
    ]
    phases = [("plus", 1.0), ("minus", -1.0), ("iplus", 1j)]
    cases: list[tuple[str, Statevector]] = []
    for left, right in pairs:
        for phase_label, phase in phases:
            cases.append(
                (
                    f"sup_{left}_{phase_label}_{right}",
                    normalized_superposition(by_label[left], by_label[right], phase),
                )
            )
    return cases


def phase_from_overlap(overlap: complex) -> complex:
    if abs(overlap) == 0:
        return 1.0 + 0.0j
    return overlap / abs(overlap)


def anchored_replay_case(
    label: str,
    input_kind: str,
    initial_state: Statevector,
    source_circuit: QuantumCircuit,
    candidate_circuit: QuantumCircuit,
    global_phase_anchor: complex,
) -> dict[str, Any]:
    source_state = initial_state.evolve(source_circuit)
    candidate_state = initial_state.evolve(candidate_circuit)
    source_data = np.asarray(source_state.data)
    candidate_data = np.asarray(candidate_state.data)
    overlap = complex(np.vdot(source_data, candidate_data))
    overlap_phase = phase_from_overlap(overlap)
    anchored_candidate = candidate_data * np.conj(global_phase_anchor)
    amplitude_delta = np.abs(source_data - anchored_candidate)
    probability_delta = np.abs(np.abs(source_data) ** 2 - np.abs(candidate_data) ** 2)
    fidelity = float(state_fidelity(source_state, candidate_state))
    phase_delta = float(np.angle(overlap_phase / global_phase_anchor))
    return {
        "label": label,
        "input_kind": input_kind,
        "overlap_magnitude": float(abs(overlap)),
        "overlap_phase_radians": float(np.angle(overlap)),
        "global_anchor_phase_delta_radians": phase_delta,
        "state_fidelity": fidelity,
        "infidelity": float(max(0.0, 1.0 - fidelity)),
        "max_global_anchor_aligned_amplitude_delta": float(np.max(amplitude_delta)),
        "max_probability_delta": float(np.max(probability_delta)),
        "passed": bool(
            abs(phase_delta) <= PHASE_TOLERANCE
            and 1.0 - fidelity <= FIDELITY_TOLERANCE
            and float(np.max(amplitude_delta)) <= AMPLITUDE_TOLERANCE
            and float(np.max(probability_delta)) <= PROBABILITY_TOLERANCE
        ),
    }


def run_probe() -> dict[str, Any]:
    candidate_payload = load_json(CANDIDATE_REWRITE_PATH)
    candidate_qasm = ROOT / candidate_payload["summary"]["qasm2_candidate_path"]
    source_circuit = load_circuit(SOURCE_QASM_PATH)
    candidate_circuit = load_circuit(candidate_qasm)
    source_unitary_part = without_final_measurements(source_circuit)
    candidate_unitary_part = without_final_measurements(candidate_circuit)
    num_qubits = source_circuit.num_qubits
    anchors = anchor_suite(num_qubits)
    zero_source = anchors[0][1].evolve(source_unitary_part)
    zero_candidate = anchors[0][1].evolve(candidate_unitary_part)
    global_phase_anchor = phase_from_overlap(
        complex(np.vdot(np.asarray(zero_source.data), np.asarray(zero_candidate.data)))
    )

    anchor_cases = [
        anchored_replay_case(
            label,
            "basis_subspace_anchor",
            state,
            source_unitary_part,
            candidate_unitary_part,
            global_phase_anchor,
        )
        for label, state in anchors
    ]
    superposition_cases = [
        anchored_replay_case(
            label,
            "coherent_pair_superposition",
            state,
            source_unitary_part,
            candidate_unitary_part,
            global_phase_anchor,
        )
        for label, state in superposition_suite(anchors)
    ]
    cases = anchor_cases + superposition_cases
    failed_cases = [case["label"] for case in cases if not case["passed"]]
    accepted_removed = 0
    summary = {
        "source_qasm": display_path(SOURCE_QASM_PATH),
        "candidate_qasm": display_path(candidate_qasm),
        "source_method": candidate_payload.get("method"),
        "source_phase_consistent_replay_method": "b1_b7_cone01_phase_consistent_replay_gate_v0",
        "qubit_count": num_qubits,
        "statevector_dimension": 2**num_qubits,
        "source_cnot_count": int(source_unitary_part.count_ops().get("cx", 0)),
        "candidate_cnot_count": int(candidate_unitary_part.count_ops().get("cx", 0)),
        "candidate_cnot_delta": int(source_unitary_part.count_ops().get("cx", 0))
        - int(candidate_unitary_part.count_ops().get("cx", 0)),
        "final_measurement_removed_for_statevector": True,
        "global_phase_anchor_label": "zero",
        "global_phase_anchor_radians": float(np.angle(global_phase_anchor)),
        "anchor_case_count": len(anchor_cases),
        "coherent_superposition_case_count": len(superposition_cases),
        "input_case_count": len(cases),
        "input_cases": cases,
        "global_phase_subspace_replay_passed": len(failed_cases) == 0,
        "failed_input_case_count": len(failed_cases),
        "failed_input_cases": failed_cases,
        "max_global_anchor_phase_delta_radians": max(
            abs(case["global_anchor_phase_delta_radians"]) for case in cases
        ),
        "min_overlap_magnitude": min(case["overlap_magnitude"] for case in cases),
        "min_state_fidelity": min(case["state_fidelity"] for case in cases),
        "max_infidelity": max(case["infidelity"] for case in cases),
        "max_global_anchor_aligned_amplitude_delta": max(
            case["max_global_anchor_aligned_amplitude_delta"] for case in cases
        ),
        "max_probability_delta": max(case["max_probability_delta"] for case in cases),
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
                "The T-B1-004av QASM2 candidate has sampled subspace replay "
                "under one global phase anchor across basis anchors and coherent "
                "pair superpositions."
            ),
            "unsupported_claims": [
                "This is not a symbolic unitary-equivalence proof for arbitrary input states.",
                "This is not an exhaustive input-space replay certificate.",
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
        "global_phase_anchor_label": "zero",
        "anchor_case_count": 6,
        "coherent_superposition_case_count": 15,
        "input_case_count": 21,
        "global_phase_subspace_replay_passed": True,
        "failed_input_case_count": 0,
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
    if float(summary.get("max_global_anchor_phase_delta_radians", 1.0)) > PHASE_TOLERANCE:
        errors.append("max_global_anchor_phase_delta_above_tolerance")
    if float(summary.get("max_infidelity", 1.0)) > FIDELITY_TOLERANCE:
        errors.append("max_infidelity_above_tolerance")
    if float(summary.get("max_global_anchor_aligned_amplitude_delta", 1.0)) > AMPLITUDE_TOLERANCE:
        errors.append("max_amplitude_delta_above_tolerance")
    if float(summary.get("max_probability_delta", 1.0)) > PROBABILITY_TOLERANCE:
        errors.append("max_probability_delta_above_tolerance")
    if summary.get("failed_input_cases") != []:
        errors.append("failed_input_cases_not_empty")
    for case in summary.get("input_cases", []):
        if case.get("passed") is not True:
            errors.append(f"case_{case.get('label')}_failed")
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
        "# B1/B7 cone_01 Global-Phase Subspace Replay Gate",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source QASM: `{summary['source_qasm']}`",
        f"- Candidate QASM: `{summary['candidate_qasm']}`",
        f"- Global phase anchor: `{summary['global_phase_anchor_label']}` / `{summary['global_phase_anchor_radians']}` radians",
        f"- Input cases: `{summary['input_case_count']}` total; `{summary['anchor_case_count']}` basis anchors and `{summary['coherent_superposition_case_count']}` coherent pair superpositions",
        f"- Global-phase subspace replay passed: `{summary['global_phase_subspace_replay_passed']}`",
        f"- Max global-anchor phase delta radians: `{summary['max_global_anchor_phase_delta_radians']}`",
        f"- Min overlap magnitude: `{summary['min_overlap_magnitude']}`",
        f"- Min fidelity / max infidelity: `{summary['min_state_fidelity']}` / `{summary['max_infidelity']}`",
        f"- Max anchored amplitude / probability delta: `{summary['max_global_anchor_aligned_amplitude_delta']}` / `{summary['max_probability_delta']}`",
        f"- Accepted full-circuit patch / replay / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_qasm_patch_count']}` / `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Input Cases",
        "",
        "| Case | Kind | Anchor phase delta | Fidelity | Max probability delta | Passed |",
        "|---|---|---:|---:|---:|---|",
    ]
    for case in summary["input_cases"]:
        lines.append(
            f"| `{case['label']}` | `{case['input_kind']}` | `{case['global_anchor_phase_delta_radians']}` | `{case['state_fidelity']}` | `{case['max_probability_delta']}` | `{case['passed']}` |"
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
            "## Interpretation",
            "",
            (
                "This gate fixes one global phase using the zero-input replay and "
                "reuses it across a small basis-anchor subspace and coherent pair "
                "superpositions. It is stronger than independently aligned sampled "
                "inputs, but it remains sampled numerical evidence with zero B7 "
                "ledger credit."
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
