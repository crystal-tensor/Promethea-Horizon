#!/usr/bin/env python3
"""R76: source-aligned replay and FT pricing for the R75 line-1378 candidate.

R75 found an exact one-CNOT pi/4-grid decomposition for the semantic packet
whose source window is lines 1369-1377.  This gate lifts that fixed witness into
the complete 19-qubit gcm_h6 circuit, exports an OpenQASM 3 companion, and
checks deterministic full-circuit replay from the benchmark input and seeded
product states.  It deliberately keeps accepted B7 credit at zero: replay
evidence and a proxy ledger delta are not the project's occurrence-removal
certificate.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Statevector, state_fidelity

from b1_b7_cone01_r75_exact_one_cnot_grid_enumeration_gate import GRID_DENOMINATOR, cost_args
from b1_b7_cone01_openqasm3_candidate_export_gate import qasm2_to_qasm3
from b7_ft_synthesis_ledger import qasm_ft_resources


ROOT = Path(__file__).resolve().parents[1]
SOURCE_QASM = ROOT / "results" / "b1_native_t_resource_optimizer" / "qasmbench_medium_exact" / "gcm_h6.qasm"
R75_JSON = ROOT / "results" / "B1_B7_cone01_R75_exact_one_cnot_grid_enumeration_gate_v0.json"
OUT_DIR = ROOT / "results" / "B1_B7_cone01_R76_line1378_grid_candidate"
QASM2_OUT = OUT_DIR / "gcm_h6_line1378_grid_candidate.qasm"
QASM3_OUT = OUT_DIR / "gcm_h6_line1378_grid_candidate_openqasm3.qasm"
JSON_OUT = ROOT / "results" / "B1_B7_cone01_R76_line1378_full_circuit_replay_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_R76_line1378_full_circuit_replay_gate.md"

METHOD = "b1_b7_cone01_r76_line1378_full_circuit_replay_gate_v0"
STATUS = "cone01_r76_line1378_full_circuit_replay_and_ft_ledger_passed_pending_b7_acceptance"
MODEL_STATUS = "r75_exact_grid_candidate_survives_full_circuit_replay_with_proxy_ft_delta_without_b7_credit"
WINDOW_START = 1369
WINDOW_END = 1377
TARGET_LINE = 1378
PHYSICAL_QUBITS = (4, 8)
PRODUCT_STATE_SEEDS = [17, 29, 41, 53, 67, 79, 83, 97]
TOLERANCE = 1e-10


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def display(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def r75_best() -> dict[str, Any]:
    payload = load_json(R75_JSON)
    row = next(row for row in payload["packet_rows"] if row["candidate_line_number"] == TARGET_LINE)
    best = row["best_exact_by_cost"]
    if best is None:
        raise ValueError("R75 line-1378 exact witness is missing")
    return {"r75": payload, "packet": row, "best": best}


def grid_expr(value: int) -> str:
    numerator = int(value)
    if numerator == 0:
        return "0"
    if numerator == GRID_DENOMINATOR:
        return "pi"
    if numerator == 2:
        return "pi/2"
    if numerator == 6:
        return "3*pi/2"
    if numerator == 4:
        return "pi"
    return f"{numerator}*pi/{GRID_DENOMINATOR}"


def u3_line(values: list[int], qubit: int) -> str:
    if len(values) != 3:
        raise ValueError("a U3 witness must have three grid values")
    args = ",".join(grid_expr(value) for value in values)
    return f"u3({args}) q[{qubit}];"


def candidate_window(best: dict[str, Any]) -> list[str]:
    left = best["left_pair_values"]
    right = best["right_pair_values"]
    if best["sequence_id"] != "01":
        raise ValueError("R76 is pinned to the R75 control-0 target-1 witness")
    return [
        u3_line(right[:3], PHYSICAL_QUBITS[0]),
        u3_line(right[3:], PHYSICAL_QUBITS[1]),
        "cx q[4],q[8];",
        u3_line(left[:3], PHYSICAL_QUBITS[0]),
        u3_line(left[3:], PHYSICAL_QUBITS[1]),
    ]


def replace_source_window(source_text: str, replacement: list[str]) -> tuple[str, dict[str, Any]]:
    lines = source_text.splitlines()
    original = lines[WINDOW_START - 1 : WINDOW_END]
    if len(original) != WINDOW_END - WINDOW_START + 1:
        raise ValueError("source window length mismatch")
    if not original[0].strip().lower().startswith("cx q[4],q[8]"):
        raise ValueError("source window anchor changed")
    if not original[-1].strip().lower().startswith("cx q[4],q[8]"):
        raise ValueError("source window terminal anchor changed")
    lines[WINDOW_START - 1 : WINDOW_END] = replacement
    return "\n".join(lines) + "\n", {
        "source_window_start_line": WINDOW_START,
        "source_window_end_line": WINDOW_END,
        "source_window_line_count": len(original),
        "replacement_line_count": len(replacement),
        "source_window_sha256": sha256_text("\n".join(original) + "\n"),
        "replacement_window_sha256": sha256_text("\n".join(replacement) + "\n"),
        "source_window": original,
        "replacement_window": replacement,
    }


def without_final_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    return circuit.remove_final_measurements(inplace=False)


def align_global_phase(reference: np.ndarray, candidate: np.ndarray) -> np.ndarray:
    inner = np.vdot(reference, candidate)
    if abs(inner) == 0:
        return candidate
    return candidate * np.conj(inner / abs(inner))


def product_state(num_qubits: int, seed: int) -> Statevector:
    rng = np.random.default_rng(seed)
    preparation = QuantumCircuit(num_qubits)
    for qubit in range(num_qubits):
        preparation.rx(float(rng.uniform(-math.pi, math.pi)), qubit)
        preparation.ry(float(rng.uniform(-math.pi, math.pi)), qubit)
        preparation.rz(float(rng.uniform(-math.pi, math.pi)), qubit)
    return Statevector.from_instruction(preparation)


def replay_case(label: str, initial: Statevector, source: QuantumCircuit, candidate: QuantumCircuit) -> dict[str, Any]:
    source_state = initial.evolve(source)
    candidate_state = initial.evolve(candidate)
    source_data = np.asarray(source_state.data)
    candidate_data = np.asarray(candidate_state.data)
    aligned = align_global_phase(source_data, candidate_data)
    amplitude_delta = np.abs(source_data - aligned)
    probability_delta = np.abs(np.abs(source_data) ** 2 - np.abs(candidate_data) ** 2)
    fidelity = float(state_fidelity(source_state, candidate_state))
    infidelity = float(max(0.0, 1.0 - fidelity))
    return {
        "label": label,
        "state_fidelity": fidelity,
        "infidelity": infidelity,
        "max_global_phase_aligned_amplitude_delta": float(np.max(amplitude_delta)),
        "l2_global_phase_aligned_amplitude_delta": float(np.linalg.norm(source_data - aligned)),
        "max_probability_delta": float(np.max(probability_delta)),
        "passed": bool(
            infidelity <= TOLERANCE
            and float(np.max(amplitude_delta)) <= TOLERANCE
            and float(np.max(probability_delta)) <= TOLERANCE
        ),
    }


def qasm_counts(circuit: QuantumCircuit) -> dict[str, int]:
    return {key: int(value) for key, value in circuit.count_ops().items()}


def compare_ft() -> dict[str, Any]:
    args = cost_args()
    source = qasm_ft_resources(SOURCE_QASM, args)
    candidate = qasm_ft_resources(QASM2_OUT, args)
    delta = {
        key: int(source[key]) - int(candidate[key])
        for key in ["operation_count_scanned", "logical_t_count_ledger", "logical_t_depth_ledger", "rotation_component_count"]
    }
    return {
        "cost_model": {
            "pi_over_4_t_cost": args.pi_over_4_t_cost,
            "pi_over_8_t_cost": args.pi_over_8_t_cost,
            "arbitrary_rotation_t_cost": args.arbitrary_rotation_t_cost,
            "unknown_rotation_t_cost": args.unknown_rotation_t_cost,
        },
        "source": source,
        "candidate": candidate,
        "source_minus_candidate": delta,
        "logical_t_count_reduced": delta["logical_t_count_ledger"] > 0,
        "logical_t_depth_reduced": delta["logical_t_depth_ledger"] > 0,
    }


def build_payload() -> dict[str, Any]:
    witness = r75_best()
    best = witness["best"]
    source_text = SOURCE_QASM.read_text(encoding="utf-8")
    replacement = candidate_window(best)
    candidate_text, window = replace_source_window(source_text, replacement)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    QASM2_OUT.write_text(candidate_text, encoding="utf-8")
    qasm3_text, conversions = qasm2_to_qasm3(candidate_text)
    QASM3_OUT.write_text(qasm3_text, encoding="utf-8")

    source_circuit = without_final_measurements(QuantumCircuit.from_qasm_file(str(SOURCE_QASM)))
    candidate_circuit = without_final_measurements(QuantumCircuit.from_qasm_file(str(QASM2_OUT)))
    qasm3_full_circuit = qasm3.loads(qasm3_text)
    qasm3_circuit = without_final_measurements(qasm3_full_circuit)
    replay_cases = [
        replay_case("benchmark_default_zero_input", Statevector.from_label("0" * source_circuit.num_qubits), source_circuit, candidate_circuit),
        *[
            replay_case(f"seeded_product_state_{seed}", product_state(source_circuit.num_qubits, seed), source_circuit, candidate_circuit)
            for seed in PRODUCT_STATE_SEEDS
        ],
    ]
    qasm3_cases = [
        replay_case("benchmark_default_zero_input", Statevector.from_label("0" * source_circuit.num_qubits), source_circuit, qasm3_circuit),
    ]
    ft = compare_ft()
    source_counts = qasm_counts(source_circuit)
    candidate_counts = qasm_counts(candidate_circuit)
    qasm3_full_counts = qasm_counts(qasm3_full_circuit)
    qasm3_counts = qasm_counts(qasm3_circuit)
    normalized_qasm3_counts = dict(qasm3_counts)
    normalized_qasm3_counts["u3"] = normalized_qasm3_counts.pop("u", 0)
    failed = [case["label"] for case in replay_cases + qasm3_cases if not case["passed"]]
    replay_passed = not failed
    summary = {
        "source_qasm": display(SOURCE_QASM),
        "candidate_qasm2": display(QASM2_OUT),
        "candidate_qasm3": display(QASM3_OUT),
        "source_sha256": sha256_text(source_text),
        "candidate_qasm2_sha256": sha256_text(candidate_text),
        "candidate_qasm3_sha256": sha256_text(qasm3_text),
        "target_line_number": TARGET_LINE,
        "source_window_start_line": WINDOW_START,
        "source_window_end_line": WINDOW_END,
        "source_line_count": len(source_text.splitlines()),
        "candidate_qasm2_line_count": len(candidate_text.splitlines()),
        "candidate_qasm3_line_count": len(qasm3_text.splitlines()),
        "source_counts_without_measurements": source_counts,
        "candidate_qasm2_counts_without_measurements": candidate_counts,
        "candidate_qasm3_counts_without_measurements": normalized_qasm3_counts,
        "source_cnot_count": int(source_counts.get("cx", 0)),
        "candidate_cnot_count": int(candidate_counts.get("cx", 0)),
        "candidate_cnot_delta": int(source_counts.get("cx", 0)) - int(candidate_counts.get("cx", 0)),
        "qasm3_counts_match_qasm2": normalized_qasm3_counts == candidate_counts,
        "candidate_qasm3_full_counts": qasm3_full_counts,
        "qasm3_conversion_count": len(conversions),
        "qiskit_version": package_version("qiskit"),
        "qiskit_qasm3_import_version": package_version("qiskit-qasm3-import"),
        "qasm3_qubit_count": int(qasm3_circuit.num_qubits),
        "qasm3_clbit_count": int(qasm3_full_circuit.num_clbits),
        "qasm3_depth_without_measurements": int(qasm3_circuit.depth()),
        "replay_case_count": len(replay_cases),
        "seeded_product_state_case_count": len(PRODUCT_STATE_SEEDS),
        "replay_cases": replay_cases,
        "qasm3_default_replay_cases": qasm3_cases,
        "replay_passed": replay_passed,
        "failed_replay_cases": failed,
        "min_state_fidelity": min(case["state_fidelity"] for case in replay_cases + qasm3_cases),
        "max_infidelity": max(case["infidelity"] for case in replay_cases + qasm3_cases),
        "max_amplitude_delta": max(case["max_global_phase_aligned_amplitude_delta"] for case in replay_cases + qasm3_cases),
        "max_probability_delta": max(case["max_probability_delta"] for case in replay_cases + qasm3_cases),
        "r75_best_witness": best,
        "window": window,
        "ft_ledger": ft,
        "accepted_full_circuit_qasm_patch_count": 1 if replay_passed else 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "symbolic_unitary_equivalence_claimed": False,
        "arbitrary_input_equivalence_claimed": False,
        "local_u3_pricing_accepted": False,
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if replay_passed else "cone01_r76_line1378_full_circuit_replay_failed",
        "model_status": MODEL_STATUS if replay_passed else "r75_grid_candidate_replay_rejected",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_r75_result": display(R75_JSON),
        "summary": summary,
        "claim_boundary": {
            "supported_claim": (
                "The fixed R75 line-1378 pi/4-grid witness can be emitted into the complete "
                "gcm_h6 source circuit, parsed as OpenQASM 2 and 3, and matches the source "
                "on the declared full-circuit replay suite to numerical tolerance. The "
                "conservative proxy FT ledger delta is reported but not promoted to B7 credit."
            ),
            "unsupported_claims": [
                "This is not a symbolic full-Hilbert-space unitary proof.",
                "This is not an accepted B7 occurrence-removal certificate.",
                "The proxy FT ledger is not a physical fault-tolerant layout result.",
                "No patent, publication, funding, or product claim follows from this gate.",
            ],
            "symbolic_unitary_equivalence_claimed": False,
            "arbitrary_input_equivalence_claimed": False,
            "local_u3_pricing_accepted": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["validation_errors"] = validate_payload(payload)
    JSON_OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    MD_OUT.write_text(render_markdown(payload), encoding="utf-8")
    if payload["validation_errors"]:
        raise SystemExit("R76 validation failed: " + "; ".join(payload["validation_errors"]))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    if payload["method"] != METHOD:
        errors.append("method_mismatch")
    if payload["status"] != STATUS:
        errors.append("status_mismatch")
    if summary["source_window_start_line"] != WINDOW_START or summary["source_window_end_line"] != WINDOW_END:
        errors.append("source_window_mismatch")
    if summary["source_cnot_count"] != 795 or summary["candidate_cnot_count"] != 792 or summary["candidate_cnot_delta"] != 3:
        errors.append("cnot_delta_mismatch")
    if summary["candidate_qasm2_counts_without_measurements"] != summary["candidate_qasm3_counts_without_measurements"]:
        errors.append("qasm2_qasm3_count_mismatch")
    if summary["qasm3_qubit_count"] != 19 or summary["qasm3_clbit_count"] != 1:
        errors.append("qasm3_register_mismatch")
    if summary["replay_passed"] is not True or summary["failed_replay_cases"]:
        errors.append("replay_suite_failed")
    if summary["accepted_full_circuit_qasm_patch_count"] != 1:
        errors.append("full_circuit_patch_not_replayed")
    for field in ["accepted_full_circuit_replay_certificate_count", "accepted_occurrence_removal", "accepted_proxy_t_reduction"]:
        if summary[field] != 0:
            errors.append(f"{field}_must_remain_zero")
    for field in ["resource_saving_claimed", "b7_ledger_improvement_claimed", "symbolic_unitary_equivalence_claimed", "arbitrary_input_equivalence_claimed", "local_u3_pricing_accepted"]:
        if summary[field] is not False or payload["claim_boundary"].get(field) is not False:
            errors.append(f"{field}_must_remain_false")
    for path in [QASM2_OUT, QASM3_OUT]:
        if not path.exists() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"missing_artifact:{display(path)}")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    ft = s["ft_ledger"]
    delta = ft["source_minus_candidate"]
    lines = [
        "# B1/B7 R76 Line-1378 Full-Circuit Replay Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- R75 source window: lines `{WINDOW_START}-{WINDOW_END}` for target packet line `{TARGET_LINE}`",
        "",
        "## Candidate",
        "",
        f"- QASM2: `{s['candidate_qasm2']}`",
        f"- QASM3: `{s['candidate_qasm3']}`",
        f"- Source/candidate CNOT count: `{s['source_cnot_count']}` / `{s['candidate_cnot_count']}`; delta `{s['candidate_cnot_delta']}`",
        f"- Candidate operation counts without measurements: `{s['candidate_qasm2_counts_without_measurements']}`",
        f"- QASM2/QASM3 counts preserved: `{s['qasm3_counts_match_qasm2']}`",
        "",
        "## Replay",
        "",
        f"- Cases: `{s['replay_case_count']}` full-circuit cases, including `{s['seeded_product_state_case_count']}` seeded product states, plus one QASM3 default-input case",
        f"- Replay passed: `{s['replay_passed']}`",
        f"- Minimum fidelity / maximum infidelity: `{s['min_state_fidelity']}` / `{s['max_infidelity']}`",
        f"- Maximum phase-aligned amplitude / probability delta: `{s['max_amplitude_delta']}` / `{s['max_probability_delta']}`",
        f"- Failed cases: `{s['failed_replay_cases']}`",
        "",
        "## FT Ledger",
        "",
        f"- Source/candidate logical T ledger: `{ft['source']['logical_t_count_ledger']}` / `{ft['candidate']['logical_t_count_ledger']}`",
        f"- Source/candidate logical T depth: `{ft['source']['logical_t_depth_ledger']}` / `{ft['candidate']['logical_t_depth_ledger']}`",
        f"- Source-minus-candidate ledger deltas: `{delta}`",
        f"- Candidate rotation families: `{ft['candidate']['rotation_family_counts']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"]["supported_claim"],
        "",
    ]
    lines.extend(f"- {claim}" for claim in payload["claim_boundary"]["unsupported_claims"])
    lines.extend([
        "",
        "Accepted full-circuit replay artifact: `1`; accepted occurrence removal, proxy-T reduction, symbolic equivalence, and B7 credit: `0`.",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    payload = build_payload()
    print(json.dumps({
        "status": payload["status"],
        "replay_passed": payload["summary"]["replay_passed"],
        "source_cnot_count": payload["summary"]["source_cnot_count"],
        "candidate_cnot_count": payload["summary"]["candidate_cnot_count"],
        "logical_t_count_before": payload["summary"]["ft_ledger"]["source"]["logical_t_count_ledger"],
        "logical_t_count_after": payload["summary"]["ft_ledger"]["candidate"]["logical_t_count_ledger"],
        "validation_errors": payload["validation_errors"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
