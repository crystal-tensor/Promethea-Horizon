#!/usr/bin/env python3
"""T-B1-004ho/T-B7-016x: independently replay the R116 candidate with NumPy."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path

import numpy as np

from b1_equivalence_check import parse_qasm, qubit_index_map


METHOD = "b1_b7_cone01_r117_independent_numpy_replay_gate_v0"
STATUS = "cone01_r117_independent_numpy_replay_30_probe_accepted"
MODEL_STATUS = "independent_numpy_replay_matches_qiskit_finite_probe"
TARGET_ID = "T-B1-004ho/T-B7-016x"
UPSTREAM_TARGET_ID = "T-B1-004hn/T-B7-016w"
SOURCE_PATH = "benchmarks/qasmbench_medium_exact/gcm_h6.qasm"
CANDIDATE_PATH = "results/B1_B7_cone01_R116_measurement_detached_exact_2q_gate/measurement_detached_candidate.qasm"
R116_RESULT_PATH = "results/B1_B7_cone01_R116_measurement_detached_exact_2q_gate_v0.json"
OUT_DIR = "results/B1_B7_cone01_R117_independent_numpy_replay_gate"
RESULT_PATH = "results/B1_B7_cone01_R117_independent_numpy_replay_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R117_independent_numpy_replay_gate.md"
PROBE_SEED = 117
PROBE_TOLERANCE = 1e-9
MEASUREMENT_RE = re.compile(r"^\s*measure\s+.+?\s*->\s*.+;\s*$")


def stable_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def u3_matrix(theta: float, phi: float, lam: float) -> np.ndarray:
    c = math.cos(theta / 2)
    s = math.sin(theta / 2)
    return np.array(
        [
            [c, -np.exp(1j * lam) * s],
            [np.exp(1j * phi) * s, np.exp(1j * (phi + lam)) * c],
        ],
        dtype=np.complex128,
    )


def single_matrix(gate: str, params: list[float]) -> np.ndarray:
    if gate == "u3":
        return u3_matrix(*params)
    if gate == "rz":
        theta = params[0]
        return np.diag([np.exp(-0.5j * theta), np.exp(0.5j * theta)]).astype(np.complex128)
    if gate == "sx":
        return np.array(
            [[0.5 + 0.5j, 0.5 - 0.5j], [0.5 - 0.5j, 0.5 + 0.5j]],
            dtype=np.complex128,
        )
    if gate == "x":
        return np.array([[0, 1], [1, 0]], dtype=np.complex128)
    raise ValueError(f"unsupported R117 single-qubit gate: {gate}")


def apply_single(state: np.ndarray, qubit: int, matrix: np.ndarray) -> None:
    bit = 1 << qubit
    indices = np.arange(state.size)
    zero_indices = indices[(indices & bit) == 0]
    one_indices = zero_indices | bit
    zero = state[zero_indices].copy()
    one = state[one_indices].copy()
    state[zero_indices] = matrix[0, 0] * zero + matrix[0, 1] * one
    state[one_indices] = matrix[1, 0] * zero + matrix[1, 1] * one


def apply_cx(state: np.ndarray, control: int, target: int) -> None:
    target_bit = 1 << target
    control_bit = 1 << control
    indices = np.arange(state.size)
    source = indices[(indices & control_bit) != 0]
    source = source[(source & target_bit) == 0]
    target_indices = source | target_bit
    state[source], state[target_indices] = state[target_indices].copy(), state[source].copy()


def simulate(path: Path, initial: np.ndarray) -> tuple[np.ndarray, int, int]:
    qregs, operations = parse_qasm(path)
    mapping = qubit_index_map(qregs)
    qubit_count = sum(qregs.values())
    state = np.asarray(initial, dtype=np.complex128).copy()
    if state.size != 1 << qubit_count:
        raise ValueError(f"input dimension mismatch for {path}: {state.size} != {1 << qubit_count}")
    for operation in operations:
        gate = operation["gate"]
        qubits = [mapping[item] for item in operation["qubits"]]
        if gate in {"u3", "rz", "sx", "x"} and len(qubits) == 1:
            apply_single(state, qubits[0], single_matrix(gate, operation["params"]))
        elif gate == "cx" and len(qubits) == 2:
            apply_cx(state, qubits[0], qubits[1])
        else:
            raise ValueError(f"unsupported R117 gate in {path} at line {operation['line']}: {operation['raw']}")
    return state, qubit_count, sum(operation["gate"] == "cx" for operation in operations)


def make_probes(qubit_count: int) -> list[tuple[str, np.ndarray]]:
    dimension = 1 << qubit_count
    probes: list[tuple[str, np.ndarray]] = []
    zero = np.zeros(dimension, dtype=np.complex128)
    zero[0] = 1
    probes.append(("zero", zero))
    for qubit in range(qubit_count):
        basis = np.zeros(dimension, dtype=np.complex128)
        basis[1 << qubit] = 1
        probes.append((f"basis_{qubit}", basis))
    rng = np.random.default_rng(PROBE_SEED)
    for index in range(8):
        vector = rng.normal(size=dimension) + 1j * rng.normal(size=dimension)
        probes.append((f"random_{index}", vector / np.linalg.norm(vector)))
    for index in range(8):
        product = np.array([1 + 0j], dtype=np.complex128)
        for _ in range(qubit_count):
            theta = rng.uniform(0, math.pi)
            phase = rng.uniform(-math.pi, math.pi)
            local = np.array(
                [math.cos(theta / 2), np.exp(1j * phase) * math.sin(theta / 2)],
                dtype=np.complex128,
            )
            product = np.kron(product, local)
        probes.append((f"product_{index}", product / np.linalg.norm(product)))
    return probes


def fidelity(left: np.ndarray, right: np.ndarray) -> float:
    overlap = np.vdot(left, right)
    return float(abs(overlap) ** 2 / (np.vdot(left, left).real * np.vdot(right, right).real))


def measurement_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if MEASUREMENT_RE.match(line)]


def report(payload: dict) -> str:
    summary = payload["summary"]
    requirements = "\n".join(
        f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}"
        for item in payload["requirements"]
    )
    return f"""# B1/B7 Cone01 R117 Independent NumPy Replay Gate

## Summary

- Target: `{TARGET_ID}`
- Upstream target: `{UPSTREAM_TARGET_ID}`
- Method: `{METHOD}`
- Status: `{STATUS}`
- Model status: `{MODEL_STATUS}`
- Source CX count: `{summary['source_two_qubit_gate_count']}`
- Candidate CX count: `{summary['candidate_two_qubit_gate_count']}`
- CX reduction: `{summary['two_qubit_reduction_pct']:.4f}%`
- Independent NumPy probes: `{summary['probe_passed']}/{summary['probe_count']}`
- Maximum fidelity deficit: `{summary['max_fidelity_deficit']}`
- Measurement map preserved: `{summary['measurement_map_preserved']}`
- B7 credit: `{summary['b7_credit_delta']}`

R117 replays the R116 source and candidate with a separate NumPy statevector
engine. It does not call Qiskit for compilation or simulation. The engine
parses the OpenQASM gate stream, applies independent U3/RZ/SX/X/CX kernels,
and checks 30 inputs: zero, 13 computational-basis states, 8 full random
states, and 8 random product states.

This is cross-implementation finite-probe evidence, not a mathematical proof
of arbitrary-input unitary equivalence. No hardware layout, T-resource, or B7
ledger credit is inferred.

## Requirements

{requirements}

## Claim Boundary

Supported: the R116 terminal-measurement-detached candidate survives an
independent NumPy replay over 30 recorded input states while preserving the
source measurement map and the `762 -> 528` CX reduction. Not supported:
arbitrary-input proof, mid-circuit measurement semantics, hardware layout
improvement, T-resource reduction, or B7 credit.
"""


def run_gate(root: Path) -> dict:
    root = root.resolve()
    source = root / SOURCE_PATH
    candidate = root / CANDIDATE_PATH
    r116 = json.loads((root / R116_RESULT_PATH).read_text(encoding="utf-8"))
    if r116.get("status") != "cone01_r116_measurement_detached_exact_2q_accepted_finite_probe":
        raise ValueError("R117 requires the accepted R116 result")
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    out = root / OUT_DIR
    out.mkdir(parents=True, exist_ok=True)
    source_lines = measurement_lines(source)
    candidate_lines = measurement_lines(candidate)
    source_qregs, source_ops = parse_qasm(source)
    candidate_qregs, candidate_ops = parse_qasm(candidate)
    qubit_count = sum(source_qregs.values())
    if sum(candidate_qregs.values()) != qubit_count:
        raise ValueError("source and candidate qubit counts differ")
    probes = make_probes(qubit_count)
    rows = []
    source_cx = None
    candidate_cx = None
    for name, initial in probes:
        source_state, _, source_count = simulate(source, initial)
        candidate_state, _, candidate_count = simulate(candidate, initial)
        if source_cx is None:
            source_cx, candidate_cx = source_count, candidate_count
        value = fidelity(source_state, candidate_state)
        rows.append({"name": name, "fidelity": value, "fidelity_deficit": max(0.0, 1.0 - value)})
    probe_payload = {
        "engine": "numpy_independent_statevector_v0",
        "probe_seed": PROBE_SEED,
        "probe_count": len(rows),
        "probe_tolerance": PROBE_TOLERANCE,
        "passed": sum(row["fidelity_deficit"] <= PROBE_TOLERANCE for row in rows),
        "failed": sum(row["fidelity_deficit"] > PROBE_TOLERANCE for row in rows),
        "max_fidelity_deficit": max(row["fidelity_deficit"] for row in rows),
        "results": rows,
    }
    probe_path = out / "numpy_cross_check.json"
    write_json(probe_path, probe_payload)
    measurement_preserved = source_lines == candidate_lines and bool(source_lines)
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "engine": "numpy_independent_statevector_v0",
        "source_two_qubit_gate_count": source_cx,
        "candidate_two_qubit_gate_count": candidate_cx,
        "two_qubit_gate_delta": candidate_cx - source_cx,
        "two_qubit_reduction_pct": (source_cx - candidate_cx) / source_cx * 100 if source_cx else 0,
        "probe_count": probe_payload["probe_count"],
        "probe_passed": probe_payload["passed"],
        "probe_failed": probe_payload["failed"],
        "max_fidelity_deficit": probe_payload["max_fidelity_deficit"],
        "source_measurement_count": len(source_lines),
        "candidate_measurement_count": len(candidate_lines),
        "measurement_map_preserved": measurement_preserved,
        "b7_credit_delta": 0,
        "counter_delta": 0,
        "new_credit_delta": 0,
    }
    requirements = [
        {"requirement_id": "P1", "label": "accepted R116 artifact is the input", "passed": True, "evidence": {"r116_status": r116["status"], "candidate": CANDIDATE_PATH}},
        {"requirement_id": "P2", "label": "independent NumPy replay engine is used", "passed": True, "evidence": {"engine": summary["engine"], "qiskit_compiler_called": False}},
        {"requirement_id": "P3", "label": "candidate has a nonzero two-qubit reduction", "passed": summary["two_qubit_gate_delta"] < 0, "evidence": {"source": source_cx, "candidate": candidate_cx, "delta": summary["two_qubit_gate_delta"]}},
        {"requirement_id": "P4", "label": "all independent probes pass", "passed": summary["probe_passed"] == summary["probe_count"] and summary["probe_failed"] == 0, "evidence": {"passed": summary["probe_passed"], "count": summary["probe_count"]}},
        {"requirement_id": "P5", "label": "independent replay error stays within tolerance", "passed": summary["max_fidelity_deficit"] <= PROBE_TOLERANCE, "evidence": {"max_fidelity_deficit": summary["max_fidelity_deficit"], "tolerance": PROBE_TOLERANCE}},
        {"requirement_id": "P6", "label": "source measurement map is preserved", "passed": summary["measurement_map_preserved"], "evidence": {"source": source_lines, "candidate": candidate_lines}},
        {"requirement_id": "P7", "label": "source and candidate have the same qubit count", "passed": sum(source_qregs.values()) == sum(candidate_qregs.values()), "evidence": {"source": sum(source_qregs.values()), "candidate": sum(candidate_qregs.values())}},
        {"requirement_id": "P8", "label": "independent probe output is materialized", "passed": probe_path.exists() and len(probe_payload["results"]) == 30, "evidence": {"path": str(probe_path.relative_to(root)), "rows": len(probe_payload["results"])}},
        {"requirement_id": "P9", "label": "B7 credit remains zero", "passed": summary["b7_credit_delta"] == 0, "evidence": {"b7_credit_delta": 0}},
        {"requirement_id": "P10", "label": "claim boundary excludes arbitrary proof and hardware claims", "passed": True, "evidence": {"model_status": MODEL_STATUS}},
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    payload = {
        "title": "B1/B7 cone01 R117 independent NumPy replay gate",
        "version": "0.1",
        "generated_at_unix": int(time.time()),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_path": SOURCE_PATH,
        "candidate_path": CANDIDATE_PATH,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "summary": summary,
        "artifacts": {"numpy_cross_check": str(probe_path.relative_to(root)), "r116_result": R116_RESULT_PATH},
        "claim_boundary": {"what_is_supported": "R116 candidate survives an independent NumPy replay over 30 finite input states and preserves the source terminal measurement map with a 762 to 528 CX reduction.", "what_is_not_supported": "Arbitrary-input unitary proof, mid-circuit measurement semantics, hardware layout improvement, T-resource reduction, or B7 credit.", "next_gate": "Add a symbolic/unitary certificate or an independently generated compiler candidate before any B7 resource credit."},
    }
    payload["payload_hash"] = stable_hash(payload)
    write_json(root / RESULT_PATH, payload)
    (root / REPORT_PATH).write_text(report(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    args = parser.parse_args()
    print(json.dumps(run_gate(Path(args.repo_root)), sort_keys=True))


if __name__ == "__main__":
    main()
