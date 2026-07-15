#!/usr/bin/env python3
"""T-B1-004fx/T-B7-015g: discrete Clifford+T scaffold pressure.

R73 showed that mixed CNOT directions do not lower the continuous FT proxy.
R74 keeps those direction sequences but restricts every local-U3 Euler angle
to an eight-point pi/4 grid.  The resulting search directly tests whether a
reduced-CNOT candidate can avoid arbitrary numeric rotations altogether.

This is a seeded finite optimization pressure test, not an exhaustive search
over all Clifford+T circuits and not a global synthesis lower bound.
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
from scipy.optimize import differential_evolution

from b1_b7_cone01_packet_synthesis_search_gate import (
    EXACT_TOLERANCE,
    cx_on,
    pair_layer,
    residual_vector,
    target_matrix,
)
from b7_ft_synthesis_ledger import rotation_cost


METHOD = "b1_b7_cone01_r74_grid_scaffold_pressure_gate_v0"
STATUS = "cone01_r74_grid_scaffold_no_exact_candidate_pressure_boundary"
MODEL_STATUS = "mixed_orientation_pi_over_four_grid_search_finds_no_exact_reduced_scaffold"
VERSION = "0.1"
TARGET_ID = "T-B1-004fx/T-B7-015g"
UPSTREAM_TARGET_ID = "T-B1-004fw/T-B7-015f"
SEMANTIC_PACKET = "results/B1_B7_cone01_semantic_replay_packet_gate_v0.json"
R73_RESULT = "results/B1_B7_cone01_R73_mixed_orientation_cost_aware_synthesis_gate_v0.json"
GRID_DENOMINATOR = 4
GRID_POINTS = tuple(range(8))
MAX_REDUCED_CNOT_COUNT = 3
DEFAULT_SEED_COUNT = 2
DEFAULT_MAXITER = 40
DEFAULT_POPSIZE = 5


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


def grid_rotation_cost(values: list[int], args: SimpleNamespace) -> dict[str, Any]:
    total = 0
    families: dict[str, int] = {}
    for value in values:
        expression = f"{int(value)}/{GRID_DENOMINATOR}*pi"
        cost, family = rotation_cost(expression, args)
        total += cost
        families[family] = families.get(family, 0) + 1
    return {
        "rotation_cost": total,
        "rotation_family_counts": dict(sorted(families.items())),
        "parameter_count": len(values),
        "grid_parameter_count": len(values),
        "arbitrary_parameter_count": 0,
    }


def mixed_scaffold_unitary(values: list[int], sequence: list[tuple[int, int]]) -> np.ndarray:
    angles = np.asarray(values, dtype=float) * math.pi / GRID_DENOMINATOR
    total = np.eye(4, dtype=complex)
    offset = 0
    for layer_index in range(len(sequence) + 1):
        total = pair_layer(angles[offset : offset + 6]) @ total
        offset += 6
        if layer_index < len(sequence):
            total = cx_on(*sequence[layer_index]) @ total
    return total


def orientation_sequences(cnot_count: int) -> list[list[tuple[int, int]]]:
    return [
        list(sequence)
        for sequence in itertools.product(((0, 1), (1, 0)), repeat=cnot_count)
    ]


def optimize_sequence(
    packet: dict[str, Any],
    sequence: list[tuple[int, int]],
    target: np.ndarray,
    seed: int,
    maxiter: int,
    popsize: int,
    args: SimpleNamespace,
) -> dict[str, Any]:
    dimension = 6 * (len(sequence) + 1)

    def objective(values: np.ndarray) -> float:
        integer_values = [int(round(value)) for value in values]
        return float(
            np.linalg.norm(residual_vector(mixed_scaffold_unitary(integer_values, sequence), target))
        )

    result = differential_evolution(
        objective,
        [(min(GRID_POINTS), max(GRID_POINTS))] * dimension,
        integrality=[True] * dimension,
        seed=seed,
        maxiter=maxiter,
        popsize=popsize,
        polish=False,
        tol=0.0,
        atol=0.0,
        workers=1,
        updating="immediate",
    )
    values = [int(round(value)) % len(GRID_POINTS) for value in result.x]
    residual = objective(np.asarray(values, dtype=float))
    return {
        "cnot_count": len(sequence),
        "cnot_sequence": [[control, target] for control, target in sequence],
        "sequence_id": "-".join(f"{control}{target}" for control, target in sequence) or "empty",
        "local_u3_layer_count": len(sequence) + 1,
        "parameter_count": dimension,
        "grid_denominator": GRID_DENOMINATOR,
        "grid_point_count_per_parameter": len(GRID_POINTS),
        "seed": seed,
        "optimizer_nfev": int(result.nfev),
        "optimizer_success": bool(result.success),
        "residual_norm": residual,
        "exact_pass": residual <= EXACT_TOLERANCE,
        "grid_values": values,
        "candidate_rotation_cost": grid_rotation_cost(values, args),
    }


def analyze_packet(
    packet: dict[str, Any],
    seed_count: int,
    maxiter: int,
    popsize: int,
    args: SimpleNamespace,
) -> dict[str, Any]:
    target = target_matrix(packet)
    source_cnot_count = int(packet["cx_count"])
    search_cnot_counts = list(range(min(MAX_REDUCED_CNOT_COUNT, source_cnot_count - 1) + 1))
    sequence_rows: list[dict[str, Any]] = []
    for cnot_count in search_cnot_counts:
        for sequence_index, sequence in enumerate(orientation_sequences(cnot_count)):
            for seed_index in range(seed_count):
                seed = (
                    74000
                    + int(packet["candidate_line_number"]) * 31
                    + cnot_count * 97
                    + sequence_index * 11
                    + seed_index
                )
                sequence_rows.append(
                    optimize_sequence(packet, sequence, target, seed, maxiter, popsize, args)
                )
    exact_rows = [row for row in sequence_rows if row["exact_pass"]]
    exact_sorted = sorted(
        exact_rows,
        key=lambda row: (
            row["candidate_rotation_cost"]["rotation_cost"],
            row["residual_norm"],
            row["cnot_count"],
        ),
    )
    best_exact = exact_sorted[0] if exact_sorted else None
    best_overall = min(sequence_rows, key=lambda row: row["residual_norm"])
    source_cost = source_rotation_cost(packet, args)
    return {
        "candidate_line_number": int(packet["candidate_line_number"]),
        "pattern_id": packet["pattern_id"],
        "source_cnot_count": source_cnot_count,
        "source_rotation_cost": source_cost,
        "search_cnot_counts": search_cnot_counts,
        "orientation_sequence_count": sum(
            len(orientation_sequences(cnot_count)) for cnot_count in search_cnot_counts
        ),
        "seed_count_per_sequence": seed_count,
        "maxiter": maxiter,
        "popsize": popsize,
        "attempt_count": len(sequence_rows),
        "exact_solution_count": len(exact_rows),
        "best_exact_by_cost": best_exact,
        "best_overall_by_residual": best_overall,
        "best_exact_rotation_cost": (
            best_exact["candidate_rotation_cost"]["rotation_cost"] if best_exact else None
        ),
        "source_minus_best_exact_rotation_cost": (
            source_cost["rotation_cost"] - best_exact["candidate_rotation_cost"]["rotation_cost"]
            if best_exact
            else None
        ),
        "sequence_rows": sequence_rows,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
    }


def build_payload(root: Path, seed_count: int, maxiter: int, popsize: int) -> dict[str, Any]:
    started = time.time()
    semantic_path = root / SEMANTIC_PACKET
    r73_path = root / R73_RESULT
    semantic = load_json(semantic_path)
    r73 = load_json(r73_path)
    args = cost_args()
    rows = [
        analyze_packet(packet, seed_count, maxiter, popsize, args)
        for packet in semantic["semantic_replay_packets"]
    ]
    exact_solution_count = sum(row["exact_solution_count"] for row in rows)
    cost_improving_count = sum(
        1
        for row in rows
        if row["best_exact_by_cost"] is not None
        and row["best_exact_by_cost"]["candidate_rotation_cost"]["rotation_cost"]
        < row["source_rotation_cost"]["rotation_cost"]
    )
    total_sequence_count = sum(row["orientation_sequence_count"] for row in rows)
    requirements = [
        req(
            "R1",
            "Three source semantic replay packets are available",
            len(rows) == 3,
            {"packet_count": len(rows), "source_method": semantic["method"]},
        ),
        req(
            "R2",
            "R73 upstream remains a verified mixed-orientation cost boundary",
            r73["summary"]["requirements_failed"] == 0
            and r73["summary"]["cost_improving_packet_count"] == 0,
            {
                "r73_requirements_failed": r73["summary"]["requirements_failed"],
                "r73_cost_improving_packet_count": r73["summary"]["cost_improving_packet_count"],
            },
        ),
        req(
            "R3",
            "The pi/4 grid and FT cost model are pinned",
            GRID_DENOMINATOR == 4
            and GRID_POINTS == tuple(range(8))
            and args.pi_over_4_t_cost == 1
            and args.pi_over_8_t_cost == 4
            and args.arbitrary_rotation_t_cost == 20
            and args.unknown_rotation_t_cost == 20,
            {
                "grid_denominator": GRID_DENOMINATOR,
                "grid_point_count": len(GRID_POINTS),
                "pi_over_4_t_cost": args.pi_over_4_t_cost,
                "pi_over_8_t_cost": args.pi_over_8_t_cost,
                "arbitrary_rotation_t_cost": args.arbitrary_rotation_t_cost,
                "unknown_rotation_t_cost": args.unknown_rotation_t_cost,
            },
        ),
        req(
            "R4",
            "All mixed direction sequences through three reduced CNOTs are enumerated",
            all(row["orientation_sequence_count"] == 15 for row in rows),
            {
                "orientation_sequences_per_packet": [row["orientation_sequence_count"] for row in rows],
                "total_orientation_sequence_count": total_sequence_count,
            },
        ),
        req(
            "R5",
            "The discrete search emits no strict exact reduced-CNOT candidate",
            exact_solution_count == 0,
            {
                "exact_solution_count": exact_solution_count,
                "best_residual_by_packet": [row["best_overall_by_residual"]["residual_norm"] for row in rows],
            },
        ),
        req(
            "R6",
            "The finite search records a nonzero residual pressure boundary",
            all(row["best_overall_by_residual"]["residual_norm"] > EXACT_TOLERANCE for row in rows),
            {
                "best_residual_by_packet": [row["best_overall_by_residual"]["residual_norm"] for row in rows],
                "exact_tolerance": EXACT_TOLERANCE,
            },
        ),
        req(
            "R7",
            "The grid search emits no accepted B7 delta",
            all(row["accepted_occurrence_removal"] == 0 for row in rows)
            and all(row["accepted_proxy_t_reduction"] == 0 for row in rows),
            {"accepted_occurrence_removal": 0, "accepted_proxy_t_reduction": 0},
        ),
        req(
            "R8",
            "The finite search is reproducibly serialized",
            all(row["attempt_count"] == row["orientation_sequence_count"] * seed_count for row in rows),
            {
                "attempt_count_by_packet": [row["attempt_count"] for row in rows],
                "seed_count_per_sequence": seed_count,
            },
        ),
    ]
    summary = {
        "packet_count": len(rows),
        "grid_denominator": GRID_DENOMINATOR,
        "grid_point_count_per_parameter": len(GRID_POINTS),
        "seed_count_per_sequence": seed_count,
        "maxiter": maxiter,
        "popsize": popsize,
        "orientation_sequences_per_packet": 15,
        "total_orientation_sequence_count": total_sequence_count,
        "total_attempt_count": sum(row["attempt_count"] for row in rows),
        "exact_solution_count": exact_solution_count,
        "cost_improving_packet_count": cost_improving_count,
        "best_residual_by_packet": [row["best_overall_by_residual"]["residual_norm"] for row in rows],
        "best_sequence_by_packet": [
            row["best_overall_by_residual"]["sequence_id"] for row in rows
        ],
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "accepted_exit_route_count": 0,
        "b7_credit_delta": 0,
        "requirements_passed": sum(1 for item in requirements if item["passed"]),
        "requirements_failed": sum(1 for item in requirements if not item["passed"]),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "global_exhaustive_claimed": False,
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
        "source_r73_result": rel(root, r73_path),
        "source_r73_result_sha256": file_hash(r73_path),
        "grid_model": {
            "angle_expression": "k*pi/4",
            "k_values": list(GRID_POINTS),
            "local_u3_parameter_count_per_layer": 6,
            "optimizer": "scipy_differential_evolution_integer_domain",
        },
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
                "In the seeded finite differential-evolution pressure test over mixed CNOT "
                "directions and pi/4-grid local-U3 angles, no strict exact reduced-CNOT "
                "candidate was found for the three semantic packets."
            ),
            "unsupported_claims": [
                "This is not exhaustive over all Clifford+T circuits or all T-depth schedules.",
                "This is not a global synthesis lower bound.",
                "This does not produce a full-circuit rewrite, occurrence removal, proxy-T reduction, reroute, or B7 credit.",
            ],
            "global_exhaustive_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["payload_hash"] = stable_hash(payload)
    return payload


def report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R74 Grid Scaffold Pressure Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Requirements: `{summary['requirements_passed']}/{len(payload['requirements'])}`",
        f"- Grid: `k*pi/4`, k in `{list(GRID_POINTS)}`",
        f"- Mixed orientation sequences per packet: `{summary['orientation_sequences_per_packet']}`",
        f"- Optimizer attempts: `{summary['total_attempt_count']}`",
        f"- Strict exact candidates: `{summary['exact_solution_count']}`",
        f"- Best residual by packet: `{summary['best_residual_by_packet']}`",
        f"- Best sequence by packet: `{summary['best_sequence_by_packet']}`",
        f"- Accepted occurrence removal / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- B7 credit: `{summary['b7_credit_delta']}`",
        "",
        "## Interpretation",
        "",
        "The finite grid pressure test found no strict exact reduced-CNOT candidate after replacing arbitrary local-U3 angles with pi/4-grid angles. This does not prove that a Clifford+T circuit cannot exist; it says the tested mixed-direction grid scaffolds did not reveal one under the declared seeds and optimizer budget.",
        "",
        "## Claim Boundary",
        "",
        "- This is a seeded finite discrete optimization pressure test, not an exhaustive Clifford+T search.",
        "- No full-circuit rewrite, occurrence removal, proxy-T reduction, reroute, or B7 credit is accepted.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--maxiter", type=int, default=DEFAULT_MAXITER)
    parser.add_argument("--popsize", type=int, default=DEFAULT_POPSIZE)
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R74_grid_scaffold_pressure_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R74_grid_scaffold_pressure_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve()
    payload = build_payload(root, args.seed_count, args.maxiter, args.popsize)
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
                    "best_residual_by_packet": payload["summary"]["best_residual_by_packet"],
                    "best_sequence_by_packet": payload["summary"]["best_sequence_by_packet"],
                    "payload_hash": payload["payload_hash"],
                },
                indent=2,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
