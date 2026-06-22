#!/usr/bin/env python3
"""Three-CNOT pricing screen for the B1/B7 cone_01 union region.

Earlier union-region gates closed the 0/1-CNOT shortcut and showed that the
2-CNOT census candidates are exact but pricing-dominated by the current
line-1381 patch. This gate changes scaffold instead of freeing more cheap
local parameters: it allows three CNOTs, searches all direction sequences, and
asks whether any exact 3-CNOT candidate has lower local-U3 proxy pressure than
the current 5-parameter / 100-proxy-T line-1381 boundary.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from scipy.optimize import least_squares

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)
from b1_b7_cone01_packet_synthesis_search_gate import (
    EXACT_TOLERANCE,
    parameter_stats,
    phase_align,
    residual_vector,
    target_matrix,
    wrap_angles,
)
from b1_b7_cone01_union_region_one_free_parameter_pricing_gate import (
    GRID_SNAP_PATH,
    SEMANTIC_PACKET_PATH,
    TARGET_LINE,
    line_packet,
)
from b1_b7_cone01_union_region_two_cnot_orientation_census_gate import (
    mixed_scaffold_unitary,
)


ROOT = Path(__file__).resolve().parents[1]
TWO_CNOT_CENSUS_PATH = (
    ROOT / "results" / "B1_B7_cone01_union_region_two_cnot_orientation_census_gate_v0.json"
)
THREE_FREE_PATH = (
    ROOT
    / "results"
    / "B1_B7_cone01_union_region_three_free_expansion_pricing_gate_v0.json"
)
JSON_OUT = (
    ROOT / "results" / "B1_B7_cone01_union_region_three_cnot_pricing_screen_gate_v0.json"
)
MD_OUT = ROOT / "research" / "B1_B7_cone01_union_region_three_cnot_pricing_screen_gate.md"

METHOD = "b1_b7_cone01_union_region_three_cnot_pricing_screen_gate_v0"
STATUS_REJECTED = "cone01_union_region_three_cnot_pricing_screen_rejected"
STATUS_CANDIDATE = "cone01_union_region_three_cnot_candidate_needs_full_circuit_pricing"
MODEL_REJECTED = "three_cnot_union_candidates_do_not_price_better_than_current_boundary"
MODEL_CANDIDATE = "three_cnot_union_candidate_is_local_exact_but_unaccepted"
DEFAULT_SEED_COUNT = 28
DEFAULT_MAX_NFEV = 3600
PROXY_T_PER_OFF_GRID_PARAMETER = 20
CURRENT_LINE1381_OFF_GRID_PARAMETER_COUNT = 5
CURRENT_LINE1381_PROXY_T_PRESSURE = 100
SEARCHED_CNOT_COUNT = 3
ORIENTATION_SEQUENCES = [
    list(sequence)
    for sequence in itertools.product([(0, 1), (1, 0)], repeat=SEARCHED_CNOT_COUNT)
]


def sequence_id(sequence: list[tuple[int, int]]) -> str:
    return "-".join(f"{control}{target}" for control, target in sequence)


def seed_points(sequence: list[tuple[int, int]], dimension: int, seed_count: int) -> list[np.ndarray]:
    signature = sum((index + 1) * (5 * control + 11 * target) for index, (control, target) in enumerate(sequence))
    rng = np.random.default_rng(41004 + signature)
    points: list[np.ndarray] = [
        np.zeros(dimension, dtype=float),
        np.full(dimension, math.pi / 4, dtype=float),
        np.full(dimension, -math.pi / 4, dtype=float),
    ]
    for scale in [0.05, 0.2, 0.75, 1.5, math.pi]:
        points.append(rng.normal(0.0, scale, size=dimension))
        points.append(rng.uniform(-scale, scale, size=dimension))
    while len(points) < seed_count:
        points.append(rng.uniform(-2.0 * math.pi, 2.0 * math.pi, size=dimension))
    return points[:seed_count]


def optimize_sequence(
    sequence: list[tuple[int, int]],
    target: np.ndarray,
    seed_count: int,
    max_nfev: int,
) -> dict[str, Any]:
    dimension = 6 * (len(sequence) + 1)

    def objective(values: np.ndarray) -> np.ndarray:
        return residual_vector(mixed_scaffold_unitary(values, sequence), target)

    attempts: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None
    for seed_index, seed in enumerate(seed_points(sequence, dimension, seed_count)):
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
        candidate = mixed_scaffold_unitary(result.x, sequence)
        max_error = float(np.max(np.abs(phase_align(candidate, target) - target)))
        attempt = {
            "seed_index": seed_index,
            "residual_norm": residual,
            "max_abs_entry_error": max_error,
            "optimizer_success": bool(result.success),
            "optimizer_nfev": int(result.nfev),
        }
        attempts.append(attempt)
        if best is None or residual < best["residual_norm"]:
            wrapped = wrap_angles(result.x)
            stats = parameter_stats(wrapped)
            off_grid = stats["off_pi_over_four_grid_parameter_count"]
            best = {
                **attempt,
                "wrapped_parameters": wrapped,
                "parameter_stats": stats,
                "proxy_t_pressure": int(off_grid * PROXY_T_PER_OFF_GRID_PARAMETER),
            }
    assert best is not None
    return {
        "sequence_id": sequence_id(sequence),
        "cnot_sequence": [[control, target_bit] for control, target_bit in sequence],
        "cnot_count": len(sequence),
        "local_u3_layer_count": len(sequence) + 1,
        "parameter_count": dimension,
        "seed_count": len(attempts),
        "best": best,
        "attempts": attempts,
        "exact_pass": best["residual_norm"] <= EXACT_TOLERANCE,
    }


def run_probe(seed_count: int, max_nfev: int) -> dict[str, Any]:
    semantic = load_json(SEMANTIC_PACKET_PATH)
    two_cnot = load_json(TWO_CNOT_CENSUS_PATH)
    grid_snap = load_json(GRID_SNAP_PATH)
    three_free = load_json(THREE_FREE_PATH)
    packet = line_packet(semantic, TARGET_LINE)
    target = target_matrix(packet)
    rows = [
        optimize_sequence(sequence, target, seed_count, max_nfev)
        for sequence in ORIENTATION_SEQUENCES
    ]
    exact_rows = [row for row in rows if row["exact_pass"]]
    best_row = min(rows, key=lambda row: row["best"]["residual_norm"])
    best_exact_row = (
        min(
            exact_rows,
            key=lambda row: (
                row["best"]["proxy_t_pressure"],
                row["best"]["parameter_stats"]["off_pi_over_four_grid_parameter_count"],
                row["best"]["residual_norm"],
            ),
        )
        if exact_rows
        else None
    )
    best_exact_proxy_t_pressure = (
        int(best_exact_row["best"]["proxy_t_pressure"]) if best_exact_row else None
    )
    best_exact_off_grid = (
        int(
            best_exact_row["best"]["parameter_stats"][
                "off_pi_over_four_grid_parameter_count"
            ]
        )
        if best_exact_row
        else None
    )
    prices_below_current = (
        best_exact_proxy_t_pressure is not None
        and best_exact_proxy_t_pressure < CURRENT_LINE1381_PROXY_T_PRESSURE
    )
    cnot_dominates_current = SEARCHED_CNOT_COUNT <= 2
    accepted_removed = 0
    candidate_found = bool(exact_rows) and prices_below_current and cnot_dominates_current
    summary = {
        "source_semantic_packet_method": semantic.get("method"),
        "source_two_cnot_census_method": two_cnot.get("method"),
        "source_grid_snap_pricing_method": grid_snap.get("method"),
        "source_three_free_expansion_method": three_free.get("method"),
        "target_line_number": TARGET_LINE,
        "union_window": [
            int(packet["window_start_line"]),
            int(packet["window_end_line"]),
        ],
        "support_qubits": packet["support_qubits"],
        "source_cnot_count": int(packet["cx_count"]),
        "searched_cnot_count": SEARCHED_CNOT_COUNT,
        "searched_orientation_sequence_count": len(rows),
        "orientation_sequence_ids": [row["sequence_id"] for row in rows],
        "search_seed_count_per_sequence": seed_count,
        "search_max_nfev": max_nfev,
        "three_cnot_exact_sequence_count": len(exact_rows),
        "three_cnot_exact_sequence_ids": [row["sequence_id"] for row in exact_rows],
        "best_sequence_id": best_row["sequence_id"],
        "best_residual_norm": best_row["best"]["residual_norm"],
        "best_max_abs_entry_error": best_row["best"]["max_abs_entry_error"],
        "best_exact_sequence_id": best_exact_row["sequence_id"] if best_exact_row else None,
        "best_exact_residual_norm": best_exact_row["best"]["residual_norm"] if best_exact_row else None,
        "best_exact_max_abs_entry_error": (
            best_exact_row["best"]["max_abs_entry_error"] if best_exact_row else None
        ),
        "best_exact_off_pi_over_four_parameter_count": best_exact_off_grid,
        "best_exact_proxy_t_pressure": best_exact_proxy_t_pressure,
        "current_line1381_off_grid_parameter_count": CURRENT_LINE1381_OFF_GRID_PARAMETER_COUNT,
        "current_line1381_proxy_t_pressure": CURRENT_LINE1381_PROXY_T_PRESSURE,
        "current_line1381_replacement_cnot_count": 2,
        "three_cnot_structurally_dominates_current_line1381_replacement": cnot_dominates_current,
        "three_cnot_prices_below_current_line1381_boundary": prices_below_current,
        "best_two_cnot_census_proxy_t_pressure": grid_snap["summary"][
            "best_source_proxy_t_pressure"
        ],
        "targeted_three_free_proxy_t_pressure_if_accepted": three_free["summary"][
            "targeted_three_free_proxy_t_pressure_if_accepted"
        ],
        "three_cnot_pricing_candidate_found": candidate_found,
        "three_cnot_pricing_accepted": False,
        "local_u3_pricing_completed": False,
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
        "status": STATUS_CANDIDATE if candidate_found else STATUS_REJECTED,
        "model_status": MODEL_CANDIDATE if candidate_found else MODEL_REJECTED,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_semantic_packet_result": display_path(SEMANTIC_PACKET_PATH),
        "source_two_cnot_census_result": display_path(TWO_CNOT_CENSUS_PATH),
        "source_grid_snap_pricing_result": display_path(GRID_SNAP_PATH),
        "source_three_free_expansion_result": display_path(THREE_FREE_PATH),
        "summary": summary,
        "union_region_three_cnot_pricing_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "Within the tested all-direction 3-CNOT local-U3 scaffold family, "
                "this gate screens whether any local exact candidate prices below "
                "the current line-1381 5-parameter / 100-proxy-T boundary while "
                "also structurally dominating the current 2-CNOT replacement."
            ),
            "unsupported_claims": [
                "This is not a global CNOT/local-U3 lower-bound theorem.",
                "A local exact 3-CNOT candidate is not a full-circuit replay certificate.",
                "A 3-CNOT union candidate does not recover extra CNOT delta over the current 2-CNOT line-1381 replacement.",
                "This does not accept occurrence removal, proxy-T reduction, or a B7 ledger improvement.",
            ],
            "three_cnot_pricing_accepted": False,
            "local_u3_pricing_completed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("union_region_three_cnot_pricing_rows", [])
    expected = {
        "target_line_number": 1381,
        "union_window": [1369, 1379],
        "support_qubits": [4, 8],
        "source_cnot_count": 5,
        "searched_cnot_count": 3,
        "searched_orientation_sequence_count": 8,
        "orientation_sequence_ids": [
            "01-01-01",
            "01-01-10",
            "01-10-01",
            "01-10-10",
            "10-01-01",
            "10-01-10",
            "10-10-01",
            "10-10-10",
        ],
        "current_line1381_off_grid_parameter_count": 5,
        "current_line1381_proxy_t_pressure": 100,
        "current_line1381_replacement_cnot_count": 2,
        "three_cnot_structurally_dominates_current_line1381_replacement": False,
        "three_cnot_pricing_accepted": False,
        "local_u3_pricing_completed": False,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_full_circuit_qasm_patch_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
    }
    if payload.get("benchmark_id") != "B1":
        errors.append("benchmark_id_mismatch")
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") not in {STATUS_REJECTED, STATUS_CANDIDATE}:
        errors.append("status_mismatch")
    if payload.get("model_status") not in {MODEL_REJECTED, MODEL_CANDIDATE}:
        errors.append("model_status_mismatch")
    for key, value in expected.items():
        if summary.get(key) != value:
            errors.append(f"summary_{key}_expected_{value!r}_got_{summary.get(key)!r}")
    if len(rows) != 8:
        errors.append(f"row_count_expected_8_got_{len(rows)}")
    exact_count = sum(1 for row in rows if row.get("exact_pass"))
    if summary.get("three_cnot_exact_sequence_count") != exact_count:
        errors.append("exact_sequence_count_mismatch")
    if summary.get("three_cnot_pricing_candidate_found") != (
        bool(exact_count)
        and summary.get("three_cnot_prices_below_current_line1381_boundary")
        and summary.get("three_cnot_structurally_dominates_current_line1381_replacement")
    ):
        errors.append("candidate_found_mismatch")
    claims = payload.get("claim_boundary", {})
    for field in [
        "three_cnot_pricing_accepted",
        "local_u3_pricing_completed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if claims.get(field) is not False:
            errors.append(f"claim_boundary_{field}_not_false")
    return errors


def markdown_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 cone_01 Union-Region Three-CNOT Pricing Screen Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Union window: `{summary['union_window']}`",
        f"- Support qubits: `{summary['support_qubits']}`",
        f"- Orientation sequences: `{summary['orientation_sequence_ids']}`",
        f"- Three-CNOT exact sequences: `{summary['three_cnot_exact_sequence_count']}`",
        f"- Best residual: `{summary['best_residual_norm']}` on `{summary['best_sequence_id']}`",
        f"- Best exact sequence: `{summary['best_exact_sequence_id']}`",
        f"- Best exact off-grid local-U3 parameters: `{summary['best_exact_off_pi_over_four_parameter_count']}`",
        f"- Best exact proxy-T pressure: `{summary['best_exact_proxy_t_pressure']}`",
        f"- Current line-1381 proxy-T pressure: `{summary['current_line1381_proxy_t_pressure']}`",
        f"- Structurally dominates current line-1381 2-CNOT replacement: `{summary['three_cnot_structurally_dominates_current_line1381_replacement']}`",
        f"- Prices below current line-1381 boundary: `{summary['three_cnot_prices_below_current_line1381_boundary']}`",
        f"- B7 ledger improvement claimed: `{summary['b7_ledger_improvement_claimed']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"]["supported_claim"],
        "",
        "Unsupported claims:",
    ]
    for claim in payload["claim_boundary"]["unsupported_claims"]:
        lines.append(f"- {claim}")
    lines.extend(["", "## Sequence Rows", ""])
    for row in payload["union_region_three_cnot_pricing_rows"]:
        stats = row["best"]["parameter_stats"]
        lines.append(
            "- "
            f"`{row['sequence_id']}`: exact `{row['exact_pass']}`, "
            f"residual `{row['best']['residual_norm']}`, "
            f"off-grid `{stats['off_pi_over_four_grid_parameter_count']}`, "
            f"proxy-T `{row['best']['proxy_t_pressure']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--seed-count", type=int, default=DEFAULT_SEED_COUNT)
    parser.add_argument("--max-nfev", type=int, default=DEFAULT_MAX_NFEV)
    args = parser.parse_args()

    payload = run_probe(args.seed_count, args.max_nfev)
    errors = validate_payload(payload)
    if errors:
        raise SystemExit("validation failed: " + "; ".join(errors))
    write_json(args.json_output, payload, True)
    write_text(args.markdown_output, markdown_report(payload))
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
