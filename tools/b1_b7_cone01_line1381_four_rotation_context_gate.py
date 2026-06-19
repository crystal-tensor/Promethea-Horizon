#!/usr/bin/env python3
"""Four-rotation context gate for the remaining line-1381 angles.

T-B1-004ap rejected signed sums of two or three nearby same-support context
rotations for the five remaining line-1381 local-U3 parameters. This gate takes
one more bounded step: can any signed sum of exactly four such context rotations
absorb a remaining parameter back to the pi/4 grid?

The result is a bounded search boundary, not a symbolic obstruction theorem or
a B7 resource claim.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    INVENTORY_QASM_PATH,
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    parse_rotation_inventory,
    wrap_angle,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
MULTI_ROTATION_CONTEXT_PATH = (
    ROOT / "results" / "B1_B7_cone01_line1381_multi_rotation_context_gate_v0.json"
)
FIVE_PARAMETER_PATH = (
    ROOT / "results" / "B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json"
)
EXACT_DECOMPOSITION_PATH = (
    ROOT / "results" / "B1_B7_cone01_line1381_exact_decomposition_pressure_gate_v0.json"
)
JSON_OUT = ROOT / "results" / "B1_B7_cone01_line1381_four_rotation_context_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_line1381_four_rotation_context_gate.md"

METHOD = "b1_b7_cone01_line1381_four_rotation_context_gate_v0"
STATUS = "cone01_line1381_four_rotation_context_not_accepted"
MODEL_STATUS = "remaining_five_line1381_parameters_have_no_four_rotation_context_absorption"
TARGET_LINE = 1381
CONTEXT_RADIUS = 64
SEARCH_WIDTH = 4
ANGLE_TOLERANCE = 1e-9


def pi_over_four_distance(value: float) -> float:
    grid = round(value / (math.pi / 4.0)) * (math.pi / 4.0)
    return abs(wrap_angle(value - grid))


def compact_context_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "line_number": row["line_number"],
        "gate": row["gate"],
        "argument_index": row["argument_index"],
        "qubit": row["qubit"],
        "raw_angle": row["raw_angle"],
        "text": row["text"],
    }


def signed_combination_count(context_count: int) -> int:
    return math.comb(context_count, SEARCH_WIDTH) * (2**SEARCH_WIDTH)


def find_four_rotation_absorptions(
    values: list[tuple[int, float]],
    context_rows: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    best_by_parameter: dict[int, dict[str, Any] | None] = {
        index: None for index, _ in values
    }
    exact_hit_count_by_parameter = {index: 0 for index, _ in values}

    for indices in itertools.combinations(range(len(context_rows)), SEARCH_WIDTH):
        selected = [context_rows[index] for index in indices]
        angles = [float(row["angle"]) for row in selected]
        for signs in itertools.product((1, -1), repeat=SEARCH_WIDTH):
            signed_sum = sum(sign * angle for sign, angle in zip(signs, angles))
            for parameter_index, value in values:
                combined = wrap_angle(value + signed_sum)
                error = pi_over_four_distance(combined)
                candidate = {
                    "width": SEARCH_WIDTH,
                    "context_lines": [row["line_number"] for row in selected],
                    "context_gates": [row["gate"] for row in selected],
                    "context_qubits": [row["qubit"] for row in selected],
                    "context_argument_indices": [row["argument_index"] for row in selected],
                    "context_raw_angles": [row["raw_angle"] for row in selected],
                    "signs": list(signs),
                    "signed_context_sum": signed_sum,
                    "combined_angle": combined,
                    "distance_to_pi_over_four_grid": error,
                    "context_rows": [compact_context_row(row) for row in selected],
                }
                best = best_by_parameter[parameter_index]
                if best is None or (
                    error,
                    tuple(int(row["line_number"]) for row in selected),
                    tuple(signs),
                ) < (
                    best["distance_to_pi_over_four_grid"],
                    tuple(int(line) for line in best["context_lines"]),
                    tuple(int(sign) for sign in best["signs"]),
                ):
                    best_by_parameter[parameter_index] = candidate
                if error <= ANGLE_TOLERANCE:
                    exact_hit_count_by_parameter[parameter_index] += 1

    return {
        index: {
            "width": SEARCH_WIDTH,
            "signed_combination_count": signed_combination_count(len(context_rows)),
            "exact_absorption_candidate_count": exact_hit_count_by_parameter[index],
            "best_absorption_candidate": best_by_parameter[index],
            "accepted_four_rotation_context_absorption": False,
        }
        for index, _ in values
    }


def build_payload() -> dict[str, Any]:
    multi_source = load_json(MULTI_ROTATION_CONTEXT_PATH)
    five_parameter = load_json(FIVE_PARAMETER_PATH)
    exact_pressure = load_json(EXACT_DECOMPOSITION_PATH)
    pressure_rows = exact_pressure["line1381_exact_decomposition_pressure_rows"]
    five_row = five_parameter["five_parameter_line1381_exact_repair_rows"][0]
    support_qubits = {int(qubit) for qubit in five_row["support_qubits"]}
    window_start = int(five_row["window_start_line"])
    window_end = int(five_row["window_end_line"])
    context_start = window_start - CONTEXT_RADIUS
    context_end = window_end + CONTEXT_RADIUS
    inventory_rows = parse_rotation_inventory(INVENTORY_QASM_PATH)
    context_rows = [
        row
        for row in inventory_rows
        if int(row["qubit"]) in support_qubits
        and context_start <= int(row["line_number"]) <= context_end
    ]
    values = [
        (int(row["parameter_index"]), float(row["parameter_value"]))
        for row in pressure_rows
    ]
    results_by_parameter = find_four_rotation_absorptions(values, context_rows)
    rows = []
    for source_row in pressure_rows:
        parameter_index = int(source_row["parameter_index"])
        value = float(source_row["parameter_value"])
        result = results_by_parameter[parameter_index]
        rows.append(
            {
                "parameter_index": parameter_index,
                "parameter_value": value,
                "value_over_pi": value / math.pi,
                "support_qubits": sorted(support_qubits),
                "context_start_line": context_start,
                "context_end_line": context_end,
                "context_rotation_argument_count": len(context_rows),
                "search_width": SEARCH_WIDTH,
                "four_rotation_result": result,
                "exact_four_rotation_absorption": False,
                "accepted_four_rotation_context_absorption": False,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
                "claim_boundary": (
                    "Four-rotation signed context sums are bounded search hints only. "
                    "They are not commutation, symbolic replay, full-circuit replay, or B7 resource certificates."
                ),
            }
        )

    accepted_removed = sum(row["accepted_occurrence_removal"] for row in rows)
    best_errors = [
        row["four_rotation_result"]["best_absorption_candidate"][
            "distance_to_pi_over_four_grid"
        ]
        for row in rows
    ]
    summary = {
        "source_multi_rotation_context_method": multi_source.get("method"),
        "source_five_parameter_line1381_exact_repair_method": five_parameter.get("method"),
        "source_exact_decomposition_pressure_method": exact_pressure.get("method"),
        "target_candidate_line_number": TARGET_LINE,
        "support_qubits": sorted(support_qubits),
        "window_start_line": window_start,
        "window_end_line": window_end,
        "context_radius": CONTEXT_RADIUS,
        "context_start_line": context_start,
        "context_end_line": context_end,
        "rotation_argument_inventory_count": len(inventory_rows),
        "context_rotation_argument_count": len(context_rows),
        "tested_remaining_parameter_count": len(rows),
        "search_width": SEARCH_WIDTH,
        "width4_signed_combination_count_per_parameter": signed_combination_count(
            len(context_rows)
        ),
        "total_signed_combination_tests": signed_combination_count(len(context_rows))
        * len(rows),
        "width4_exact_absorption_parameter_count": sum(
            1
            for row in rows
            if row["four_rotation_result"]["exact_absorption_candidate_count"] > 0
        ),
        "four_rotation_exact_absorption_parameter_count": sum(
            1 for row in rows if row["exact_four_rotation_absorption"]
        ),
        "min_best_width4_context_grid_error": min(best_errors),
        "max_best_width4_context_grid_error": max(best_errors),
        "accepted_four_rotation_context_absorption_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": accepted_removed,
        "accepted_proxy_t_reduction": accepted_removed * PROXY_T_PER_OCCURRENCE,
        "missing_occurrences_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed),
        "missing_proxy_t_after_gate": max(0, REQUIRED_OCCURRENCE_REMOVALS - accepted_removed)
        * PROXY_T_PER_OCCURRENCE,
        "four_rotation_context_absorption_claimed": False,
        "full_circuit_rewrite_claimed": False,
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
        "inventory_qasm": display_path(INVENTORY_QASM_PATH),
        "source_multi_rotation_context_result": display_path(MULTI_ROTATION_CONTEXT_PATH),
        "source_five_parameter_line1381_exact_repair_result": display_path(FIVE_PARAMETER_PATH),
        "source_exact_decomposition_pressure_result": display_path(EXACT_DECOMPOSITION_PATH),
        "summary": summary,
        "line1381_four_rotation_context_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The five remaining line-1381 parameters have no exact four-rotation "
                "signed same-support context absorption back to the pi/4 grid inside the configured window."
            ),
            "unsupported_claims": [
                "This is not a global obstruction theorem for line 1381.",
                "This does not reject five-or-more-rotation symbolic absorption.",
                "This does not reject commutation-aware or full-circuit replay routes.",
                "No B7 occurrence or proxy-T ledger reduction is accepted.",
            ],
            "four_rotation_context_absorption_claimed": False,
            "full_circuit_rewrite_claimed": False,
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
    }
    payload["summary"]["validation_error_count"] = len(validate_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload.get("summary", {})
    rows = payload.get("line1381_four_rotation_context_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "target_candidate_line_number": TARGET_LINE,
        "support_qubits": [4, 8],
        "window_start_line": 1369,
        "window_end_line": 1379,
        "context_radius": 64,
        "context_start_line": 1305,
        "context_end_line": 1443,
        "rotation_argument_inventory_count": 2049,
        "context_rotation_argument_count": 44,
        "tested_remaining_parameter_count": 5,
        "search_width": 4,
        "width4_signed_combination_count_per_parameter": 2172016,
        "total_signed_combination_tests": 10860080,
        "width4_exact_absorption_parameter_count": 0,
        "four_rotation_exact_absorption_parameter_count": 0,
        "accepted_four_rotation_context_absorption_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": 30,
        "missing_proxy_t_after_gate": 600,
    }
    for field, expected_value in expected.items():
        if summary.get(field) != expected_value:
            errors.append(f"{field}_expected_{expected_value}_got_{summary.get(field)}")
    if len(rows) != 5:
        errors.append(f"row_count_expected_5_got_{len(rows)}")
    else:
        if [row.get("parameter_index") for row in rows] != [3, 4, 9, 16, 17]:
            errors.append("parameter_indices_mismatch")
        for row in rows:
            if row.get("accepted_four_rotation_context_absorption") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_must_not_accept_absorption")
            if row.get("exact_four_rotation_absorption") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_must_not_exact_absorb")
            result = row.get("four_rotation_result", {})
            if result.get("exact_absorption_candidate_count") != 0:
                errors.append(
                    f"parameter_{row.get('parameter_index')}_width4_must_have_zero_hits"
                )
            if result.get("accepted_four_rotation_context_absorption") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_width4_must_not_accept")
    for field in [
        "four_rotation_context_absorption_claimed",
        "full_circuit_rewrite_claimed",
        "resource_saving_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field}_must_be_false")
        if payload.get("claim_boundary", {}).get(field) is not False:
            errors.append(f"claim_boundary_{field}_must_be_false")
    return errors


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    rows = payload["line1381_four_rotation_context_rows"]
    lines = [
        "# B1/B7 Cone_01 Line-1381 Four-Rotation Context Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004ap and tests whether the five remaining line-1381 local-U3 parameters can be absorbed by signed sums of exactly four nearby same-support context rotations in the native optimized `gcm_h6` QASM.",
        "",
        "## Summary",
        "",
        f"- Target candidate line: `{summary['target_candidate_line_number']}`",
        f"- Support qubits: `{summary['support_qubits']}`",
        f"- Source window: `{summary['window_start_line']}`-`{summary['window_end_line']}`",
        f"- Context radius: `+/-{summary['context_radius']}` lines",
        f"- Context rotation arguments reviewed: `{summary['context_rotation_argument_count']}`",
        f"- Parameters tested: `{summary['tested_remaining_parameter_count']}`",
        f"- Signed width-4 combinations per parameter: `{summary['width4_signed_combination_count_per_parameter']}`",
        f"- Total signed combination tests: `{summary['total_signed_combination_tests']}`",
        f"- Width-4 exact absorption parameters: `{summary['width4_exact_absorption_parameter_count']}`",
        f"- Min / max best width-4 grid error: `{summary['min_best_width4_context_grid_error']:.12e}` / `{summary['max_best_width4_context_grid_error']:.12e}`",
        f"- Accepted replay / occurrence / proxy-T reduction: `{summary['accepted_full_circuit_replay_certificate_count']}` / `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Parameter Rows",
        "",
        "| Param index | Value/pi | Best width-4 error | Best lines | Accepted |",
        "|---:|---:|---:|---|---|",
    ]
    for row in rows:
        best = row["four_rotation_result"]["best_absorption_candidate"]
        lines.append(
            f"| {row['parameter_index']} | {row['value_over_pi']:.12f} | "
            f"{best['distance_to_pi_over_four_grid']:.6e} | "
            f"{best['context_lines']} | {row['accepted_four_rotation_context_absorption']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This closes only a bounded exactly-four-rotation context-combination route. It does not rule out five-or-more-rotation symbolic absorption, commutation-aware rewriting, broader symbolic synthesis, or full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.",
            "",
            "## Next Required Gate",
            "",
            "The next route must either build a commutation-aware symbolic/full-circuit replay certificate for the repaired packet route, move to a deliberately justified five-or-more-rotation symbolic search, or abandon this local context route and find a different occurrence-removing scaffold with honest B7 resource accounting.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=JSON_OUT)
    parser.add_argument("--markdown-output", type=Path, default=MD_OUT)
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_payload()
    errors = validate_payload(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    if errors:
        payload["validation_errors"] = errors
    write_json(args.json_output, payload, pretty=args.pretty)
    write_text(args.markdown_output, render_markdown(payload))
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
