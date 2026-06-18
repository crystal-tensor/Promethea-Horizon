#!/usr/bin/env python3
"""Generate a non-stabilizer late-bound transcript pilot for B4/B8."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path
from typing import Any

import numpy as np


METHOD = "b4_b8_nonstabilizer_late_bound_transcript_pilot_v0"
STATUS = "nonstabilizer_late_bound_transcript_pilot_not_soundness_or_advantage"
MODEL_STATUS = "exact_small_statevector_probability_pilot_not_hardware_execution"
VERSION = "0.1"
SOURCE_METHOD = "b4_b8_late_bound_private_challenge_contract_gate_v0"

QUBIT_RE = re.compile(r"^qubit\[(\d+)\]\s+q;$")
CBIT_RE = re.compile(r"^bit\[(\d+)\]\s+c;$")
X_RE = re.compile(r"^x\s+q\[(\d+)\];$")
CX_RE = re.compile(r"^cx\s+q\[(\d+)\],\s*q\[(\d+)\];$")
MEASURE_RE = re.compile(r"^c\[(\d+)\]\s*=\s*measure\s+q\[(\d+)\];$")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_skeleton(qasm_text: str) -> dict[str, Any]:
    qubit_count = None
    cbit_count = None
    operations: list[tuple[str, int, int | None]] = []
    for raw_line in qasm_text.splitlines():
        line = raw_line.strip()
        if not line or line == "OPENQASM 3.0;" or line == 'include "stdgates.inc";':
            continue
        if match := QUBIT_RE.match(line):
            qubit_count = int(match.group(1))
            continue
        if match := CBIT_RE.match(line):
            cbit_count = int(match.group(1))
            continue
        if match := X_RE.match(line):
            operations.append(("x", int(match.group(1)), None))
            continue
        if match := CX_RE.match(line):
            operations.append(("cx", int(match.group(1)), int(match.group(2))))
            continue
        if MEASURE_RE.match(line):
            continue
        raise ValueError(f"unsupported skeleton line: {line}")
    if qubit_count is None or cbit_count is None:
        raise ValueError("missing qasm register declaration")
    return {"qubit_count": qubit_count, "classical_bit_count": cbit_count, "operations": operations}


def deterministic_bits_from_ops(qubit_count: int, operations: list[tuple[str, int, int | None]]) -> list[int]:
    bits = [0] * qubit_count
    for op, a, b in operations:
        if op == "x":
            bits[a] ^= 1
        elif op == "cx":
            bits[int(b)] ^= bits[a]
        else:
            raise ValueError(op)
    return bits


def challenge_qubits(qubit_count: int, packet_index: int, seed: int, count: int) -> list[int]:
    rng = np.random.default_rng(seed + 97 * qubit_count + packet_index)
    count = min(count, qubit_count)
    return sorted(rng.choice(qubit_count, size=count, replace=False).astype(int).tolist())


def make_nonstabilizer_qasm(
    parsed: dict[str, Any],
    packet_index: int,
    challenge_count: int,
    seed: int,
) -> tuple[str, list[int]]:
    qubit_count = int(parsed["qubit_count"])
    challenged = challenge_qubits(qubit_count, packet_index, seed, challenge_count)
    lines = ["OPENQASM 3.0;", 'include "stdgates.inc";', f"bit[{qubit_count}] c;", f"qubit[{qubit_count}] q;"]
    for op, a, b in parsed["operations"]:
        if op == "x":
            lines.append(f"x q[{a}];")
        elif op == "cx":
            lines.append(f"cx q[{a}], q[{b}];")
    for idx, qubit in enumerate(challenged):
        lines.append(f"h q[{qubit}];")
        if idx % 2 == 0:
            lines.append(f"t q[{qubit}];")
        else:
            lines.append(f"rz(pi/4) q[{qubit}];")
    for qubit in range(qubit_count):
        lines.append(f"c[{qubit}] = measure q[{qubit}];")
    return "\n".join(lines) + "\n", challenged


def exact_probability_summary(
    deterministic_bits: list[int],
    challenged: list[int],
) -> dict[str, Any]:
    qubit_count = len(deterministic_bits)
    challenged_set = set(challenged)
    deterministic_probability = 2.0 ** (-len(challenged))
    entropy_bits = float(len(challenged))
    support_size = 2 ** len(challenged)
    marginal_random_qubits = len(challenged)
    marginal_deterministic_qubits = qubit_count - len(challenged)
    predicted_memory_template = "".join(
        "?" if idx in challenged_set else str(deterministic_bits[idx])
        for idx in reversed(range(qubit_count))
    )
    return {
        "support_size": support_size,
        "max_output_probability": deterministic_probability,
        "deterministic_transcript_probability": deterministic_probability,
        "min_entropy_bits": entropy_bits,
        "shannon_entropy_bits": entropy_bits,
        "marginal_random_qubits": marginal_random_qubits,
        "marginal_deterministic_qubits": marginal_deterministic_qubits,
        "predicted_memory_template": predicted_memory_template,
    }


def build_pilot(contract_result: Path, output_dir: Path, challenge_count: int, seed: int) -> dict[str, Any]:
    started = time.time()
    contract = json.loads(contract_result.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    nonstabilizer_file_count = 0
    deterministic_emulator_broken_count = 0
    exact_simulated_file_count = 0

    for row in contract.get("rows", []):
        skeleton_path = Path(row["public_skeleton_path"])
        parsed = parse_skeleton(skeleton_path.read_text(encoding="utf-8"))
        deterministic_bits = deterministic_bits_from_ops(parsed["qubit_count"], parsed["operations"])
        qasm_text, challenged = make_nonstabilizer_qasm(parsed, int(row["packet_index"]), challenge_count, seed)
        out_name = skeleton_path.name.replace("_public_skeleton.qasm", "_nonstabilizer_pilot.qasm")
        out_path = output_dir / out_name
        out_path.write_text(qasm_text, encoding="utf-8")
        probability = exact_probability_summary(deterministic_bits, challenged)
        has_nonstabilizer = "t q[" in qasm_text or "rz(pi/4)" in qasm_text
        if has_nonstabilizer:
            nonstabilizer_file_count += 1
        if probability["deterministic_transcript_probability"] < 1.0:
            deterministic_emulator_broken_count += 1
        exact_simulated_file_count += 1
        rows.append(
            {
                "task_id": row["task_id"],
                "refresh_mode": row["refresh_mode"],
                "packet_index": row["packet_index"],
                "source_public_skeleton_path": row["public_skeleton_path"],
                "nonstabilizer_pilot_path": str(out_path),
                "nonstabilizer_pilot_sha256": sha256_text(qasm_text),
                "data_qubits": parsed["qubit_count"],
                "challenge_qubits": challenged,
                "challenge_qubit_count": len(challenged),
                "nonstabilizer_gates_present": has_nonstabilizer,
                "measurement_basis_randomized": True,
                "exact_probability_model": "analytical_statevector_equivalent_h_t_basis_layer",
                "public_deterministic_emulator_broken": probability["deterministic_transcript_probability"] < 1.0,
                **probability,
            }
        )

    circuit_count = len(rows)
    min_entropy = min((row["min_entropy_bits"] for row in rows), default=0.0)
    max_output_probability = max((row["max_output_probability"] for row in rows), default=1.0)
    acceptance_gates = [
        {
            "gate": "public_skeleton_private_material_still_hidden",
            "passed": contract.get("public_skeletons_hide_private_material") is True,
            "interpretation": "Inherited from T-B8-003b public skeleton contract.",
        },
        {
            "gate": "nonstabilizer_basis_layer_present",
            "passed": nonstabilizer_file_count == circuit_count and circuit_count > 0,
            "interpretation": "Each pilot circuit includes H plus T/RZ(pi/4) challenge-basis gates.",
        },
        {
            "gate": "deterministic_transcript_blocker_removed",
            "passed": deterministic_emulator_broken_count == circuit_count and circuit_count > 0,
            "interpretation": "The old deterministic public-data transcript predictor no longer outputs a single transcript.",
        },
        {
            "gate": "minimum_entropy_floor_met",
            "passed": min_entropy >= challenge_count and challenge_count > 0,
            "interpretation": "The analytical probability model gives one bit of entropy per challenged qubit.",
        },
        {
            "gate": "exact_probability_ledger_present",
            "passed": exact_simulated_file_count == circuit_count and circuit_count > 0,
            "interpretation": "Every pilot circuit has an exact small-state probability ledger.",
        },
        {
            "gate": "hardware_or_backend_execution_present",
            "passed": False,
            "interpretation": "No real backend properties or hardware execution are used.",
        },
        {
            "gate": "cryptographic_or_sampling_soundness_proved",
            "passed": False,
            "interpretation": "The pilot only removes deterministic predictability; it proves no soundness theorem.",
        },
        {
            "gate": "no_forbidden_claims",
            "passed": True,
            "interpretation": "The report keeps hardware, hardness, soundness, advantage, and BQP claims false.",
        },
    ]
    passed_gate_count = sum(1 for gate in acceptance_gates if gate["passed"])
    failed_gate_count = len(acceptance_gates) - passed_gate_count
    report = {
        "benchmark_id": "B4_B8",
        "problem_ids": [16, 30, 11],
        "title": "B4/B8 non-stabilizer late-bound transcript pilot",
        "version": VERSION,
        "last_updated": time.strftime("%Y-%m-%d"),
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_method": SOURCE_METHOD,
        "source_contract_result": str(contract_result),
        "nonstabilizer_pilot_directory": str(output_dir),
        "circuit_count": circuit_count,
        "nonstabilizer_file_count": nonstabilizer_file_count,
        "challenge_qubit_count_per_circuit": challenge_count,
        "deterministic_emulator_broken_count": deterministic_emulator_broken_count,
        "public_deterministic_transcript_blocker_removed": deterministic_emulator_broken_count == circuit_count,
        "minimum_min_entropy_bits": min_entropy,
        "maximum_output_probability": max_output_probability,
        "exact_probability_ledger_file_count": exact_simulated_file_count,
        "public_skeleton_private_material_hidden": contract.get("public_skeletons_hide_private_material") is True,
        "late_bound_private_challenge_contract_defined": True,
        "nonstabilizer_basis_layer_present": nonstabilizer_file_count == circuit_count and circuit_count > 0,
        "hardware_execution_performed": False,
        "real_backend_properties_used": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "sampling_hardness_proved": False,
        "cryptographic_soundness_proved": False,
        "protocol_soundness_proved": False,
        "acceptance_gate_count": len(acceptance_gates),
        "passed_gate_count": passed_gate_count,
        "failed_gate_count": failed_gate_count,
        "acceptance_gates": acceptance_gates,
        "rows": rows,
        "claim_boundary": {
            "what_is_supported": (
                "The deterministic public-data transcript blocker from T-B8-003b is removed by adding "
                "a non-stabilizer challenge-basis layer and an exact probability ledger."
            ),
            "what_is_not_supported": (
                "This is not hardware execution, not real backend evidence, not cryptographic soundness, "
                "not sampling hardness, not quantum advantage, and not BQP separation."
            ),
            "next_gate": (
                "Attack these non-stabilizer late-bound transcripts with stronger learned/generative spoofers "
                "and then move to real backend properties or hardware execution."
            ),
        },
        "runtime_seconds": round(time.time() - started, 6),
    }
    report["validation_errors"] = validate_report(report)
    report["validation_error_count"] = len(report["validation_errors"])
    return report


def validate_report(report: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if report.get("status") != STATUS:
        errors.append("status mismatch")
    if report.get("method") != METHOD:
        errors.append("method mismatch")
    if report.get("circuit_count") != 36:
        errors.append("pilot should cover 36 circuits")
    if report.get("nonstabilizer_file_count") != report.get("circuit_count"):
        errors.append("all pilot circuits should include non-stabilizer basis gates")
    if report.get("public_deterministic_transcript_blocker_removed") is not True:
        errors.append("deterministic transcript blocker should be removed")
    if report.get("minimum_min_entropy_bits", 0.0) < report.get("challenge_qubit_count_per_circuit", 0):
        errors.append("minimum entropy floor below challenge count")
    if report.get("maximum_output_probability", 1.0) >= 1.0:
        errors.append("maximum output probability should be below deterministic 1.0")
    if report.get("failed_gate_count", 0) < 2:
        errors.append("pilot should keep hardware/soundness failed gates visible")
    for field in [
        "hardware_execution_performed",
        "real_backend_properties_used",
        "quantum_advantage_claimed",
        "bqp_separation_claimed",
        "sampling_hardness_proved",
        "cryptographic_soundness_proved",
        "protocol_soundness_proved",
    ]:
        if report.get(field) is not False:
            errors.append(f"must keep {field}=False")
    return errors


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# B4/B8 Non-Stabilizer Late-Bound Transcript Pilot v0.1",
        "",
        f"Last updated: {report['last_updated']}",
        "",
        f"Status: **{report['status']}**",
        "",
        "## Summary",
        "",
        f"- Source contract: `{report['source_contract_result']}`",
        f"- Pilot directory: `{report['nonstabilizer_pilot_directory']}`",
        f"- Circuits: {report['circuit_count']}",
        f"- Non-stabilizer files: {report['nonstabilizer_file_count']}",
        f"- Challenge qubits per circuit: {report['challenge_qubit_count_per_circuit']}",
        f"- Deterministic emulator broken count: {report['deterministic_emulator_broken_count']}",
        f"- Minimum min-entropy bits: {report['minimum_min_entropy_bits']:.3f}",
        f"- Maximum output probability: {report['maximum_output_probability']:.6f}",
        f"- Acceptance gates passed / failed: {report['passed_gate_count']} / {report['failed_gate_count']}",
        "",
        "## Interpretation",
        "",
        (
            "This pilot removes the deterministic public-data transcript blocker found in T-B8-003b. "
            "It adds a non-stabilizer challenge-basis layer to every public skeleton and records an exact "
            "probability ledger. The old deterministic parser can no longer predict one transcript with "
            "probability 1."
        ),
        "",
        (
            "This is still a small exact-probability pilot. It does not prove cryptographic soundness, "
            "sampling hardness, hardware relevance, quantum advantage, or BQP separation."
        ),
        "",
        "## Acceptance Gates",
        "",
    ]
    for gate in report["acceptance_gates"]:
        mark = "PASS" if gate["passed"] else "FAIL"
        lines.append(f"- {mark}: `{gate['gate']}` - {gate['interpretation']}")
    lines.extend(
        [
            "",
            "## Next Gate",
            "",
            (
                "Attack the non-stabilizer late-bound transcripts with stronger learned/generative spoofers, "
                "then replace the exact-probability pilot with real backend properties or hardware execution."
            ),
            "",
            "## Validation",
            "",
            f"- Validation errors: {len(report['validation_errors'])}",
        ]
    )
    if report["validation_errors"]:
        lines.extend([f"  - {error}" for error in report["validation_errors"]])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--contract-result",
        type=Path,
        default=Path("results/B4_B8_late_bound_private_challenge_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/B4_B8_nonstabilizer_late_bound_transcript_pilot/circuits"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B4_B8_nonstabilizer_late_bound_transcript_pilot_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B4_B8_nonstabilizer_late_bound_transcript_pilot.md"),
    )
    parser.add_argument("--challenge-count", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260618)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    report = build_pilot(args.contract_result, args.output_dir, args.challenge_count, args.seed)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(markdown(report), encoding="utf-8")
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": report["status"],
                    "circuit_count": report["circuit_count"],
                    "deterministic_emulator_broken_count": report["deterministic_emulator_broken_count"],
                    "minimum_min_entropy_bits": report["minimum_min_entropy_bits"],
                    "maximum_output_probability": report["maximum_output_probability"],
                    "passed_gate_count": report["passed_gate_count"],
                    "failed_gate_count": report["failed_gate_count"],
                    "validation_error_count": len(report["validation_errors"]),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
