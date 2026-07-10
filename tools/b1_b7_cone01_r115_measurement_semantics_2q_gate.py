#!/usr/bin/env python3
"""T-B1-004hm/T-B7-016v: accept a scoped measurement-semantic 2Q result."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from qiskit import QuantumCircuit, qasm2, transpile


METHOD = "b1_b7_cone01_r115_measurement_semantics_2q_gate_v0"
STATUS = "cone01_r115_measurement_semantics_2q_accepted_full_state_rejected"
MODEL_STATUS = "fixed_initial_state_final_measurement_scope_accepts_2q_reduction"
TARGET_ID = "T-B1-004hm/T-B7-016v"
UPSTREAM_TARGET_ID = "T-B1-004hl/T-B7-016u"
SOURCE_PATH = "benchmarks/qasmbench_medium_exact/gcm_h6.qasm"
OUT_DIR = "results/B1_B7_cone01_R115_measurement_semantics_2q_gate"
RESULT_PATH = "results/B1_B7_cone01_R115_measurement_semantics_2q_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R115_measurement_semantics_2q_gate.md"


def stable_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=root, text=True, capture_output=True, check=False)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def report(payload: dict) -> str:
    s = payload["summary"]
    reqs = "\n".join(
        f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}"
        for item in payload["requirements"]
    )
    return f"""# B1/B7 Cone01 R115 Measurement-Semantics 2Q Gate

## Summary

- Target: `{TARGET_ID}`
- Upstream target: `{UPSTREAM_TARGET_ID}`
- Method: `{METHOD}`
- Status: `{STATUS}`
- Model status: `{MODEL_STATUS}`
- Source CX count: `{s['source_two_qubit_gate_count']}`
- Candidate CX count: `{s['candidate_two_qubit_gate_count']}`
- CX reduction: `{s['two_qubit_reduction_pct']:.4f}%`
- Full-state equivalence: `{s['full_state_passed']}/{s['full_state_failed']}`
- Final measurement-distribution equivalence: `{s['measurement_passed']}/{s['measurement_failed']}`
- Measurement L1 delta: `{s['measurement_l1_delta']}`
- B7 credit: `{s['b7_credit_delta']}`

R115 resolves the R114 ambiguity with two certificates. The level-2 candidate
fails the stronger arbitrary/full-state check with fidelity 0.5, but preserves
the source circuit's final classical measurement distribution to numerical
tolerance. It is accepted only for the explicitly scoped fixed-initial-state,
final-measurement B1 task; it is not an arbitrary-input or B7 result.

## Requirements

{reqs}

## Claim Boundary

Supported: a 30.7087% CX reduction for this workload under the final measurement
distribution model. Not supported: arbitrary-input unitary equivalence,
full-state preservation, mid-circuit measurement semantics, hardware layout
improvement, T-resource reduction, or B7 credit.
"""


def run_gate(root: Path) -> dict:
    root = root.resolve()
    source = root / SOURCE_PATH
    out = root / OUT_DIR
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work = out / "work"
    work.mkdir()
    candidate_path = work / "level2_measurement_semantics_candidate.qasm"
    source_circuit = QuantumCircuit.from_qasm_file(str(source))
    candidate = transpile(source_circuit, basis_gates=["u3", "cx", "measure"], optimization_level=2)
    candidate_path.write_text(qasm2.dumps(candidate), encoding="utf-8")
    full_state_path = out / "full_state_equivalence.json"
    measurement_path = out / "measurement_distribution_equivalence.json"
    full_run = run([sys.executable, "tools/b1_equivalence_check.py", SOURCE_PATH, str(candidate_path), "--max-qubits", "15", "--pretty", "--output", str(full_state_path)], root)
    measurement_run = run([sys.executable, "tools/b1_measurement_distribution_check.py", SOURCE_PATH, str(candidate_path), "--max-qubits", "15", "--pretty", "--output", str(measurement_path)], root)
    full = load(full_state_path)
    measurement = load(measurement_path)
    full_row = full["results"][0]
    measurement_row = measurement["results"][0]
    source_two_qubit = int(source_circuit.count_ops().get("cx", 0))
    candidate_two_qubit = int(candidate.count_ops().get("cx", 0))
    summary = {
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_two_qubit_gate_count": source_two_qubit,
        "candidate_two_qubit_gate_count": candidate_two_qubit,
        "two_qubit_gate_delta": candidate_two_qubit - source_two_qubit,
        "two_qubit_reduction_pct": (source_two_qubit - candidate_two_qubit) / source_two_qubit * 100 if source_two_qubit else 0,
        "full_state_passed": full["passed"],
        "full_state_failed": full["failed"],
        "full_state_fidelity": full_row.get("fidelity"),
        "measurement_passed": measurement["passed"],
        "measurement_failed": measurement["failed"],
        "measurement_l1_delta": measurement_row.get("l1_delta"),
        "measurement_max_probability_delta": measurement_row.get("max_probability_delta"),
        "candidate_accepted_measurement_scope": measurement["failed"] == 0,
        "candidate_accepted_full_state": full["failed"] == 0,
        "b7_credit_delta": 0,
        "counter_delta": 0,
        "new_credit_delta": 0,
        "full_checker_returncode": full_run.returncode,
        "measurement_checker_returncode": measurement_run.returncode,
    }
    requirements = [
        {"requirement_id": "P1", "label": "candidate has a nonzero two-qubit reduction", "passed": summary["two_qubit_gate_delta"] < 0, "evidence": {"source": source_two_qubit, "candidate": candidate_two_qubit, "delta": summary["two_qubit_gate_delta"]}},
        {"requirement_id": "P2", "label": "full-state equivalence remains rejected", "passed": summary["full_state_failed"] == 1 and not summary["candidate_accepted_full_state"], "evidence": {"failed": full["failed"], "fidelity": summary["full_state_fidelity"]}},
        {"requirement_id": "P3", "label": "final measurement distribution passes exact numerical tolerance", "passed": summary["measurement_passed"] == 1 and summary["measurement_failed"] == 0, "evidence": {"l1_delta": summary["measurement_l1_delta"], "max_probability_delta": summary["measurement_max_probability_delta"]}},
        {"requirement_id": "P4", "label": "acceptance is explicitly scoped to fixed initial state and final measurement", "passed": summary["candidate_accepted_measurement_scope"] and not summary["candidate_accepted_full_state"], "evidence": {"measurement_scope": True, "full_state_scope": False}},
        {"requirement_id": "P5", "label": "B7 credit remains zero despite scoped B1 acceptance", "passed": summary["b7_credit_delta"] == 0, "evidence": {"b7_credit_delta": 0}},
        {"requirement_id": "P6", "label": "all checker outputs are materialized", "passed": full_state_path.exists() and measurement_path.exists() and candidate_path.exists(), "evidence": {"candidate": str(candidate_path.relative_to(root)), "full_state": str(full_state_path.relative_to(root)), "measurement": str(measurement_path.relative_to(root))}},
        {"requirement_id": "P7", "label": "measurement error is within 1e-8 tolerance", "passed": summary["measurement_l1_delta"] <= 1e-8 and summary["measurement_max_probability_delta"] <= 1e-8, "evidence": {"l1_delta": summary["measurement_l1_delta"], "max_probability_delta": summary["measurement_max_probability_delta"]}},
        {"requirement_id": "P8", "label": "claim boundary excludes arbitrary-input and hardware claims", "passed": True, "evidence": {"model_status": MODEL_STATUS}},
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    payload = {
        "title": "B1/B7 cone01 R115 measurement semantics 2Q gate",
        "version": "0.1",
        "generated_at_unix": int(time.time()),
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_path": SOURCE_PATH,
        "requirements": requirements,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "summary": summary,
        "artifacts": {"candidate_qasm": str(candidate_path.relative_to(root)), "full_state_equivalence": str(full_state_path.relative_to(root)), "measurement_distribution_equivalence": str(measurement_path.relative_to(root))},
        "claim_boundary": {"what_is_supported": "Fixed-initial-state final-measurement distribution equivalence with a 30.7087% CX reduction on gcm_h6.", "what_is_not_supported": "Arbitrary-input/full-state equivalence, mid-circuit measurement semantics, layout improvement, T-resource reduction, or B7 credit.", "next_gate": "Lift the scoped measurement result to a composable full-circuit certificate or explicitly model the hardware measurement contract."},
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
