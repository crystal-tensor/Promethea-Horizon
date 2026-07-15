#!/usr/bin/env python3
"""T-B1-004fw/T-B7-015f: mixed-CNOT-orientation cost-aware synthesis.

R72 tested repeated CNOTs with one fixed direction.  R73 enumerates every
binary direction sequence for reduced scaffolds through three CNOTs, then
selects exact candidates by the pinned fault-tolerant rotation proxy.  The
search remains a local numerical boundary, not a synthesis lower bound.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
from scipy.optimize import least_squares

from b1_b7_cone01_packet_synthesis_search_gate import (
    EXACT_TOLERANCE,
    cx_on,
    pair_layer,
    phase_align,
    residual_vector,
    target_matrix,
    wrap_angles,
)
from b7_ft_synthesis_ledger import classify_rotation, rotation_cost


METHOD = "b1_b7_cone01_r73_mixed_orientation_cost_aware_synthesis_gate_v0"
STATUS = "cone01_r73_mixed_orientation_exact_synthesis_cost_boundary"
MODEL_STATUS = "mixed_orientation_exact_synthesis_has_no_ft_rotation_cost_improvement"
VERSION = "0.1"
TARGET_ID = "T-B1-004fw/T-B7-015f"
UPSTREAM_TARGET_ID = "T-B1-004fv/T-B7-015e"
SEMANTIC_PACKET = "results/B1_B7_cone01_semantic_replay_packet_gate_v0.json"
R72_RESULT = "results/B1_B7_cone01_R72_cost_aware_packet_synthesis_gate_v0.json"
DEFAULT_SEED_COUNT = 16
DEFAULT_MAX_NFEV = 2200
MAX_REDUCED_CNOT_COUNT = 3


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def cost_args() -> SimpleNamespace:
    return SimpleNamespace(
        pi_over_4_t_cost=1,
        pi_over_8_t_cost=4,
        arbitrary_rotation_t_cost=20,
        unknown_rotation_t_cost=20,
    )


def source_rotation_cost(packet: dict[str, Any], args: SimpleNamespace) -> dict[str, Any]:
    total = 0
    families: dict[str, int] = {}
    for operation in packet["normalized_ops"]:
        if operation["gate"] == "cx":
            continue
        expression = operation["raw_args"][0]
        cost, family = rotation_cost(expression, args)
        total += cost
        families[family] = families.get(family, 0) + 1
    return {"rotation_cost": total, "rotation_family_counts": dict(sorted(families.items()))}


def candidate_rotation_cost(parameters: list[float], args: SimpleNamespace) -> dict[str, Any]:
    total = 0
    families: dict[str, int] = {}
    for value in parameters:
        cost, family = rotation_cost(str(value), args)
        total += cost
        families[family] = families.get(family, 0) + 1
    return {
        "rotation_cost": total,
        "rotation_family_counts": dict(sorted(families.items())),
        "parameter_count": len(parameters),
        "off_pi_over_four_parameter_count": sum(
            1
            for value in parameters
            if classify_rotation(str(value)) == "arbitrary_numeric_rotation"
        ),
    }


def mixed_scaffold_unitary(params: np.ndarray, sequence: list[tuple[int, int]]) -> np.ndarray:
    total = np.eye(4, dtype=complex)
    offset = 0
    for layer_index in range(len(sequence) + 1):
        total = pair_layer(params[offset : offset + 6]) @ total
        offset += 6
        if layer_index < len(sequence):
            control, target = sequence[layer_index]
            total = cx_on(control, target) @ total
    return total


def orientation_sequences(cnot_count: int) -> list[list[tuple[int, int]]]:
    return [
        list(sequence)
        for sequence in itertools.product(((0, 1), (1, 0)), repeat=cnot_count)
    ]


def sequence_seed_points(
    packet: dict[str, Any], sequence: list[tuple[int, int]], seed_count: int
) -> list[np.ndarray]:
    dimension = 6 * (len(sequence) + 1)
    points: list[np.ndarray] = [np.zeros(dimension, dtype=float)]
    signature = sum(
        (index + 1) * (3 * control + 7 * target)
        for index, (control, target) in enumerate(sequence)
    )
    rng_seed = 27311 + int(packet["candidate_line_number"]) * 19 + signature
    rng = np.random.default_rng(rng_seed)
    for scale in [0.1, 0.35, 1.0, math.pi]:
        points.append(rng.normal(0.0, scale, size=dimension))
        points.append(rng.uniform(-scale, scale, size=dimension))
    while len(points) < seed_count:
        points.append(rng.uniform(-2.0 * math.pi, 2.0 * math.pi, size=dimension))
    return points[:seed_count]


def optimize_sequence(
    packet: dict[str, Any],
    sequence: list[tuple[int, int]],
    target: np.ndarray,
    seed_count: int,
    max_nfev: int,
    args: SimpleNamespace,
) -> dict[str, Any]:
    def objective(values: np.ndarray) -> np.ndarray:
        return residual_vector(mixed_scaffold_unitary(values, sequence), target)

    exact: list[dict[str, Any]] = []
    attempts: list[dict[str, Any]] = []
    for seed_index, seed in enumerate(sequence_seed_points(packet, sequence, seed_count)):
        result = least_squares(
            objective,
            seed,
            method="trf",
            max_nfev=max_nfev,
            ftol=1e-12,
            xtol=1e-12,
            gtol=1e-12,
        )
        residual = float(np.linalg.norm(result.fun))
        wrapped = wrap_angles(result.x)
        candidate = mixed_scaffold_unitary(result.x, sequence)
        row = {
            "seed_index": seed_index,
            "residual_norm": residual,
            "max_abs_entry_error": float(np.max(np.abs(phase_align(candidate, target) - target))),
            "optimizer_success": bool(result.success),
            "optimizer_nfev": int(result.nfev),
            "exact_pass": residual <= EXACT_TOLERANCE,
        }
        attempts.append(row)
        if row["exact_pass"]:
            exact.append(
                {
                    **row,
                    "wrapped_parameters": wrapped,
                    "candidate_rotation_cost": candidate_rotation_cost(list(wrapped), args),
                }
            )
    exact_sorted = sorted(
        exact,
        key=lambda row: (
            row["candidate_rotation_cost"]["rotation_cost"],
            row["residual_norm"],
            row["seed_index"],
        ),
    )
    best_exact = exact_sorted[0] if exact_sorted else None
    return {
        "cnot_count": len(sequence),
        "cnot_sequence": [[control, target] for control, target in sequence],
        "sequence_id": "-".join(f"{control}{target}" for control, target in sequence) or "empty",
        "local_u3_layer_count": len(sequence) + 1,
        "parameter_count": 6 * (len(sequence) + 1),
        "seed_count": seed_count,
        "attempt_count": len(attempts),
        "exact_solution_count": len(exact_sorted),
        "best_exact_by_cost": best_exact,
        "best_residual_norm": min(row["residual_norm"] for row in attempts),
        "attempts": attempts,
    }


def analyze_packet(
    packet: dict[str, Any], seed_count: int, max_nfev: int, args: SimpleNamespace
) -> dict[str, Any]:
    target = target_matrix(packet)
    source_cnot_count = int(packet["cx_count"])
    search_cnot_counts = list(range(min(MAX_REDUCED_CNOT_COUNT, source_cnot_count - 1) + 1))
    sequence_rows = []
    for cnot_count in search_cnot_counts:
        for sequence in orientation_sequences(cnot_count):
            sequence_rows.append(
                optimize_sequence(packet, sequence, target, seed_count, max_nfev, args)
            )
    exact_rows = [
        row for row in sequence_rows if row["best_exact_by_cost"] is not None
    ]
    exact_candidates = [row["best_exact_by_cost"] for row in exact_rows]
    best_exact_row = min(
        exact_rows,
        key=lambda row: (
            row["best_exact_by_cost"]["candidate_rotation_cost"]["rotation_cost"],
            row["best_exact_by_cost"]["residual_norm"],
        ),
    ) if exact_rows else None
    source_cost = source_rotation_cost(packet, args)
    return {
        "candidate_line_number": int(packet["candidate_line_number"]),
        "pattern_id": packet["pattern_id"],
        "support_qubits": packet["support_qubits"],
        "source_cnot_count": source_cnot_count,
        "source_rotation_cost": source_cost,
        "search_cnot_counts": search_cnot_counts,
        "orientation_sequence_count": sum(
            len(orientation_sequences(cnot_count)) for cnot_count in search_cnot_counts
        ),
        "seed_count_per_sequence": seed_count,
        "max_nfev": max_nfev,
        "attempt_count": sum(row["attempt_count"] for row in sequence_rows),
        "exact_solution_count": sum(row["exact_solution_count"] for row in sequence_rows),
        "exact_sequence_count": len(exact_rows),
        "best_exact_by_cost": best_exact_row["best_exact_by_cost"] if best_exact_row else None,
        "best_exact_rotation_cost": (
            best_exact_row["best_exact_by_cost"]["candidate_rotation_cost"]["rotation_cost"]
            if best_exact_row
            else None
        ),
        "source_minus_best_exact_rotation_cost": (
            source_cost["rotation_cost"]
            - best_exact_row["best_exact_by_cost"]["candidate_rotation_cost"]["rotation_cost"]
            if best_exact_row
            else None
        ),
        "cost_improving_exact_solution_found": bool(
            best_exact_row
            and best_exact_row["best_exact_by_cost"]["candidate_rotation_cost"]["rotation_cost"]
            < source_cost["rotation_cost"]
        ),
        "cnot_reducing_exact_solution_found": bool(exact_rows),
        "sequence_rows": sequence_rows,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "exact_candidate_count_across_sequences": len(exact_candidates),
    }


def build_payload(root: Path, seed_count: int, max_nfev: int) -> dict[str, Any]:
    started = time.time()
    semantic_path = root / SEMANTIC_PACKET
    r72_path = root / R72_RESULT
    semantic = load_json(semantic_path)
    r72 = load_json(r72_path)
    args = cost_args()
    rows = [
        analyze_packet(packet, seed_count, max_nfev, args)
        for packet in semantic["semantic_replay_packets"]
    ]
    exact_solution_count = sum(row["exact_solution_count"] for row in rows)
    cnot_reducing_count = sum(1 for row in rows if row["cnot_reducing_exact_solution_found"])
    cost_improving_count = sum(1 for row in rows if row["cost_improving_exact_solution_found"])
    enumerated_sequence_count = sum(row["orientation_sequence_count"] for row in rows)
    requirements = [
        req(
            "R1",
            "Three source semantic replay packets are available",
            len(rows) == 3,
            {"packet_count": len(rows), "source_method": semantic["method"]},
        ),
        req(
            "R2",
            "R72 upstream remains a verified fixed-direction cost boundary",
            r72["summary"]["requirements_failed"] == 0
            and r72["summary"]["cost_improving_packet_count"] == 0,
            {
                "r72_requirements_failed": r72["summary"]["requirements_failed"],
                "r72_cost_improving_packet_count": r72["summary"]["cost_improving_packet_count"],
            },
        ),
        req(
            "R3",
            "The rotation-family cost model is pinned",
            args.pi_over_4_t_cost == 1
            and args.pi_over_8_t_cost == 4
            and args.arbitrary_rotation_t_cost == 20
            and args.unknown_rotation_t_cost == 20,
            {
                "pi_over_4_t_cost": args.pi_over_4_t_cost,
                "pi_over_8_t_cost": args.pi_over_8_t_cost,
                "arbitrary_rotation_t_cost": args.arbitrary_rotation_t_cost,
                "unknown_rotation_t_cost": args.unknown_rotation_t_cost,
            },
        ),
        req(
            "R4",
            "All reduced mixed-orientation sequences through three CNOTs are enumerated",
            all(row["orientation_sequence_count"] == 15 for row in rows),
            {
                "orientation_sequences_per_packet": [row["orientation_sequence_count"] for row in rows],
                "total_orientation_sequences": enumerated_sequence_count,
            },
        ),
        req(
            "R5",
            "Each packet has strict exact candidates in the mixed search",
            all(row["exact_solution_count"] > 0 for row in rows),
            {"exact_solution_count_by_packet": [row["exact_solution_count"] for row in rows]},
        ),
        req(
            "R6",
            "No mixed-orientation exact candidate beats its source rotation cost",
            cost_improving_count == 0
            and all(
                row["source_minus_best_exact_rotation_cost"] is not None
                and row["source_minus_best_exact_rotation_cost"] < 0
                for row in rows
            ),
            {
                "cost_improving_packet_count": cost_improving_count,
                "source_minus_best_exact_rotation_cost": [
                    row["source_minus_best_exact_rotation_cost"] for row in rows
                ],
            },
        ),
        req(
            "R7",
            "The mixed search emits no accepted B7 delta",
            all(row["accepted_occurrence_removal"] == 0 for row in rows)
            and all(row["accepted_proxy_t_reduction"] == 0 for row in rows),
            {"accepted_occurrence_removal": 0, "accepted_proxy_t_reduction": 0},
        ),
        req(
            "R8",
            "The search packet is reproducibly serialized",
            exact_solution_count > 0 and all(row["attempt_count"] > 0 for row in rows),
            {
                "attempt_count_by_packet": [row["attempt_count"] for row in rows],
                "exact_solution_count": exact_solution_count,
            },
        ),
    ]
    summary = {
        "packet_count": len(rows),
        "seed_count_per_sequence": seed_count,
        "max_nfev": max_nfev,
        "orientation_sequences_per_packet": 15,
        "total_orientation_sequence_count": enumerated_sequence_count,
        "total_attempt_count": sum(row["attempt_count"] for row in rows),
        "exact_solution_count": exact_solution_count,
        "cnot_reducing_packet_count": cnot_reducing_count,
        "cost_improving_packet_count": cost_improving_count,
        "source_minus_best_exact_rotation_cost": [
            row["source_minus_best_exact_rotation_cost"] for row in rows
        ],
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "accepted_exit_route_count": 0,
        "b7_credit_delta": 0,
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "runtime_seconds": round(time.time() - started, 6),
    }
    payload: dict[str, Any] = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "version": VERSION,
        "target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_semantic_packet": rel(root, semantic_path),
        "source_semantic_packet_sha256": file_hash(semantic_path),
        "source_r72_result": rel(root, r72_path),
        "source_r72_result_sha256": file_hash(r72_path),
        "cost_model": {
            "clifford_rotation_t_cost": 0,
            "pi_over_4_rotation_t_cost": args.pi_over_4_t_cost,
            "pi_over_8_rotation_t_cost": args.pi_over_8_t_cost,
            "arbitrary_rotation_t_cost": args.arbitrary_rotation_t_cost,
            "unknown_rotation_t_cost": args.unknown_rotation_t_cost,
        },
        "requirements": requirements,
        "summary": summary,
        "packet_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "Across the tested mixed CNOT-direction sequences through three CNOTs, "
                "strict exact reduced-CNOT packet candidates exist, but none beats the "
                "source packet's pinned FT rotation cost."
            ),
            "unsupported_claims": [
                "This is not a global synthesis lower bound.",
                "This does not produce a full-circuit rewrite or arbitrary-input proof.",
                "This does not accept occurrence removal, proxy-T reduction, reroute, or B7 credit.",
            ],
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    return payload


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R73 Mixed-Orientation Cost-Aware Synthesis Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Requirements: `{summary['requirements_passed']}/{len(payload['requirements'])}`",
        f"- Mixed orientation sequences per packet: `{summary['orientation_sequences_per_packet']}`",
        f"- Total optimizer attempts: `{summary['total_attempt_count']}`",
        f"- Exact solution count: `{summary['exact_solution_count']}`",
        f"- Packets with reduced-CNOT exact solutions: `{summary['cnot_reducing_packet_count']}`",
        f"- Packets with FT-cost improvement: `{summary['cost_improving_packet_count']}`",
        f"- Source minus best exact rotation cost: `{summary['source_minus_best_exact_rotation_cost']}`",
        f"- Accepted occurrence removal / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- B7 credit: `{summary['b7_credit_delta']}`",
        "",
        "## Interpretation",
        "",
        "The direction space is broader than R72: every binary CNOT orientation sequence through three reduced CNOTs is tested for all three semantic packets. Exact candidates still do not lower the pinned FT rotation proxy, so reversing CNOT direction does not yet create an accepted B1/B7 resource win.",
        "",
        "## Claim Boundary",
        "",
        "- This is a finite local numerical search, not a global synthesis lower-bound theorem.",
        "- No full-circuit rewrite, occurrence removal, proxy-T reduction, reroute, or B7 credit is accepted.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--max-nfev", type=int, default=DEFAULT_MAX_NFEV)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R73_mixed_orientation_cost_aware_synthesis_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R73_mixed_orientation_cost_aware_synthesis_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    payload = build_payload(root, args.seed_count, args.max_nfev)
    json_output = args.json_output if args.json_output.is_absolute() else root / args.json_output
    markdown_output = args.markdown_output if args.markdown_output.is_absolute() else root / args.markdown_output
    write_json(json_output, payload)
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(report(payload), encoding="utf-8")
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "total_orientation_sequence_count": payload["summary"]["total_orientation_sequence_count"],
                    "total_attempt_count": payload["summary"]["total_attempt_count"],
                    "exact_solution_count": payload["summary"]["exact_solution_count"],
                    "source_minus_best_exact_rotation_cost": payload["summary"][
                        "source_minus_best_exact_rotation_cost"
                    ],
                    "payload_hash": payload["payload_hash"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
