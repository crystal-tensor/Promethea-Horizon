#!/usr/bin/env python3
"""Exact-decomposition pressure gate for the remaining line-1381 local-U3 angles.

T-B1-004am narrowed the cone_01 resource boundary to five remaining off-grid
local-U3 parameters on line 1381. This gate tests whether those five angles can
be accepted by simple exact-decomposition or source-absorption contracts before
they are allowed to affect the B7 ledger.

The result is intentionally conservative: passing the bounded packet repair is
not enough. Accepted B7 resource movement requires exact symbolic
decomposition, absorption, or a full-circuit replay certificate.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from b1_b7_cone01_carrier_absorption_inventory_gate import (
    PROXY_T_PER_OCCURRENCE,
    REQUIRED_OCCURRENCE_REMOVALS,
    display_path,
    load_json,
    write_json,
    write_text,
)


ROOT = Path(__file__).resolve().parents[1]
REPAIRED_BOUNDARY_PATH = (
    ROOT / "results" / "B1_B7_cone01_repaired_packet_resource_boundary_gate_v0.json"
)
FIVE_PARAMETER_PATH = (
    ROOT / "results" / "B1_B7_cone01_five_parameter_line1381_exact_repair_gate_v0.json"
)
JSON_OUT = ROOT / "results" / "B1_B7_cone01_line1381_exact_decomposition_pressure_gate_v0.json"
MD_OUT = ROOT / "research" / "B1_B7_cone01_line1381_exact_decomposition_pressure_gate.md"

METHOD = "b1_b7_cone01_line1381_exact_decomposition_pressure_gate_v0"
STATUS = "cone01_line1381_exact_decomposition_pressure_not_accepted"
MODEL_STATUS = "remaining_five_line1381_parameters_fail_simple_exact_decomposition_contracts"
TARGET_LINE = 1381
PI_OVER_FOUR_TOLERANCE = 1e-9
RATIONAL_PI_TOLERANCE = 1e-9
MAX_POWER_OF_TWO_DENOMINATOR = 64
MAX_RATIONAL_PI_DENOMINATOR = 512


def nearest_pi_grid(value: float, denominator: int) -> dict[str, Any]:
    numerator = round((value / math.pi) * denominator)
    reconstructed = numerator * math.pi / denominator
    return {
        "numerator": numerator,
        "denominator": denominator,
        "reconstructed_value": reconstructed,
        "absolute_error": abs(value - reconstructed),
    }


def best_rational_pi(value: float, max_denominator: int) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    for denominator in range(1, max_denominator + 1):
        candidate = nearest_pi_grid(value, denominator)
        if best is None or candidate["absolute_error"] < best["absolute_error"]:
            best = candidate
    if best is None:
        raise ValueError("max_denominator must be positive")
    return best


def best_power_of_two_pi(value: float, max_denominator: int) -> dict[str, Any]:
    best: dict[str, Any] | None = None
    denominator = 1
    while denominator <= max_denominator:
        candidate = nearest_pi_grid(value, denominator)
        if best is None or candidate["absolute_error"] < best["absolute_error"]:
            best = candidate
        denominator *= 2
    if best is None:
        raise ValueError("max_denominator must be positive")
    return best


def line1381_repaired_row(repaired_payload: dict[str, Any]) -> dict[str, Any]:
    for row in repaired_payload.get("repaired_packet_resource_boundary_rows", []):
        if row.get("candidate_line_number") == TARGET_LINE:
            return row
    raise ValueError(f"missing repaired resource-boundary row for line {TARGET_LINE}")


def line1381_five_parameter_row(five_payload: dict[str, Any]) -> dict[str, Any]:
    for row in five_payload.get("five_parameter_line1381_exact_repair_rows", []):
        if row.get("candidate_line_number") == TARGET_LINE:
            return row
    raise ValueError(f"missing five-parameter exact-repair row for line {TARGET_LINE}")


def analyze_parameter(index: int, value: float, source_off_grid_count: int) -> dict[str, Any]:
    pi_over_four = nearest_pi_grid(value, 4)
    power_two = best_power_of_two_pi(value, MAX_POWER_OF_TWO_DENOMINATOR)
    rational = best_rational_pi(value, MAX_RATIONAL_PI_DENOMINATOR)
    pi_over_four_exact = pi_over_four["absolute_error"] <= PI_OVER_FOUR_TOLERANCE
    power_two_exact = power_two["absolute_error"] <= RATIONAL_PI_TOLERANCE
    rational_exact = rational["absolute_error"] <= RATIONAL_PI_TOLERANCE
    source_absorbed = False
    return {
        "parameter_index": index,
        "parameter_value": value,
        "value_over_pi": value / math.pi,
        "nearest_pi_over_four_numerator": pi_over_four["numerator"],
        "nearest_pi_over_four_error": pi_over_four["absolute_error"],
        "pi_over_four_exact": pi_over_four_exact,
        "best_power_of_two_pi_numerator": power_two["numerator"],
        "best_power_of_two_pi_denominator": power_two["denominator"],
        "best_power_of_two_pi_error": power_two["absolute_error"],
        "power_of_two_pi_exact": power_two_exact,
        "best_rational_pi_numerator": rational["numerator"],
        "best_rational_pi_denominator": rational["denominator"],
        "best_rational_pi_error": rational["absolute_error"],
        "rational_pi_exact": rational_exact,
        "source_absorption_available": source_off_grid_count > 0,
        "source_absorbed": source_absorbed,
        "accepted_exact_decomposition": (
            pi_over_four_exact or power_two_exact or rational_exact or source_absorbed
        ),
    }


def build_payload() -> dict[str, Any]:
    repaired_payload = load_json(REPAIRED_BOUNDARY_PATH)
    five_payload = load_json(FIVE_PARAMETER_PATH)
    repaired_row = line1381_repaired_row(repaired_payload)
    five_row = line1381_five_parameter_row(five_payload)
    values = [float(value) for value in five_row["first_exact_five_parameter_free_values"]]
    indices = [int(index) for index in five_row["first_exact_five_parameter_free_indices"]]
    source_off_grid_count = int(repaired_row["source_off_pi_over_four_parameter_count"])
    rows = [
        analyze_parameter(index, value, source_off_grid_count)
        for index, value in zip(indices, values)
    ]
    accepted_count = sum(1 for row in rows if row["accepted_exact_decomposition"])
    pi_over_four_count = sum(1 for row in rows if row["pi_over_four_exact"])
    power_two_count = sum(1 for row in rows if row["power_of_two_pi_exact"])
    rational_count = sum(1 for row in rows if row["rational_pi_exact"])
    absorbed_count = sum(1 for row in rows if row["source_absorbed"])
    accepted_occurrences = 0
    summary = {
        "source_repaired_packet_resource_boundary_method": repaired_payload.get("method"),
        "source_five_parameter_line1381_exact_repair_method": five_payload.get("method"),
        "target_candidate_line_number": TARGET_LINE,
        "remaining_off_grid_parameter_count": len(values),
        "tested_remaining_parameter_count": len(rows),
        "remaining_parameter_indices": indices,
        "pi_over_four_tolerance": PI_OVER_FOUR_TOLERANCE,
        "rational_pi_tolerance": RATIONAL_PI_TOLERANCE,
        "max_power_of_two_denominator": MAX_POWER_OF_TWO_DENOMINATOR,
        "max_rational_pi_denominator": MAX_RATIONAL_PI_DENOMINATOR,
        "pi_over_four_exact_parameter_count": pi_over_four_count,
        "power_of_two_pi_exact_parameter_count": power_two_count,
        "rational_pi_exact_parameter_count": rational_count,
        "source_absorbed_parameter_count": absorbed_count,
        "accepted_exact_decomposition_parameter_count": accepted_count,
        "remaining_unaccepted_parameter_count": len(values) - accepted_count,
        "max_nearest_pi_over_four_error": max(row["nearest_pi_over_four_error"] for row in rows),
        "min_best_rational_pi_error": min(row["best_rational_pi_error"] for row in rows),
        "max_best_rational_pi_error": max(row["best_rational_pi_error"] for row in rows),
        "accepted_symbolic_decomposition_count": 0,
        "accepted_source_absorption_count": 0,
        "accepted_full_circuit_replay_certificate_count": 0,
        "accepted_occurrence_removal": accepted_occurrences,
        "accepted_proxy_t_reduction": 0,
        "missing_occurrences_after_gate": max(
            0, REQUIRED_OCCURRENCE_REMOVALS - accepted_occurrences
        ),
        "missing_proxy_t_after_gate": max(
            0,
            (REQUIRED_OCCURRENCE_REMOVALS - accepted_occurrences) * PROXY_T_PER_OCCURRENCE,
        ),
        "simple_exact_decomposition_claimed": False,
        "source_absorption_claimed": False,
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
        "source_repaired_packet_resource_boundary_result": display_path(REPAIRED_BOUNDARY_PATH),
        "source_five_parameter_line1381_exact_repair_result": display_path(FIVE_PARAMETER_PATH),
        "summary": summary,
        "line1381_exact_decomposition_pressure_rows": rows,
        "claim_boundary": {
            "supported_claim": (
                "The five remaining line-1381 off-grid local-U3 parameters fail the simple "
                "pi/4-grid, low-denominator power-of-two pi-grid, rational-pi, and source-"
                "absorption acceptance contracts used by this gate."
            ),
            "unsupported_claims": [
                "This is not a global impossibility theorem for line 1381.",
                "This does not reject broader symbolic synthesis or context absorption.",
                "No full-circuit replay certificate is accepted.",
                "No B7 occurrence or proxy-T ledger reduction is accepted.",
            ],
            "simple_exact_decomposition_claimed": False,
            "source_absorption_claimed": False,
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
    rows = payload.get("line1381_exact_decomposition_pressure_rows", [])
    if payload.get("method") != METHOD:
        errors.append("method_mismatch")
    if payload.get("status") != STATUS:
        errors.append("status_mismatch")
    expected = {
        "target_candidate_line_number": TARGET_LINE,
        "remaining_off_grid_parameter_count": 5,
        "tested_remaining_parameter_count": 5,
        "remaining_parameter_indices": [3, 4, 9, 16, 17],
        "pi_over_four_exact_parameter_count": 0,
        "power_of_two_pi_exact_parameter_count": 0,
        "rational_pi_exact_parameter_count": 0,
        "source_absorbed_parameter_count": 0,
        "accepted_exact_decomposition_parameter_count": 0,
        "remaining_unaccepted_parameter_count": 5,
        "accepted_symbolic_decomposition_count": 0,
        "accepted_source_absorption_count": 0,
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
            if row.get("accepted_exact_decomposition") is not False:
                errors.append(f"parameter_{row.get('parameter_index')}_must_not_be_accepted")
            for field in [
                "pi_over_four_exact",
                "power_of_two_pi_exact",
                "rational_pi_exact",
                "source_absorbed",
            ]:
                if row.get(field) is not False:
                    errors.append(f"parameter_{row.get('parameter_index')}_{field}_must_be_false")
    for field in [
        "simple_exact_decomposition_claimed",
        "source_absorption_claimed",
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
    rows = payload["line1381_exact_decomposition_pressure_rows"]
    lines = [
        "# B1/B7 Cone_01 Line-1381 Exact-Decomposition Pressure Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact consumes T-B1-004am and tests the five remaining off-grid local-U3 parameters on line 1381 against simple exact-decomposition and source-absorption contracts.",
        "",
        "## Summary",
        "",
        f"- Target candidate line: `{summary['target_candidate_line_number']}`",
        f"- Remaining off-grid parameters tested: `{summary['tested_remaining_parameter_count']}`",
        f"- Parameter indices: `{summary['remaining_parameter_indices']}`",
        f"- Pi/4 exact parameters: `{summary['pi_over_four_exact_parameter_count']}`",
        f"- Power-of-two pi-grid exact parameters: `{summary['power_of_two_pi_exact_parameter_count']}`",
        f"- Rational-pi exact parameters: `{summary['rational_pi_exact_parameter_count']}`",
        f"- Source-absorbed parameters: `{summary['source_absorbed_parameter_count']}`",
        f"- Accepted exact decompositions: `{summary['accepted_exact_decomposition_parameter_count']}`",
        f"- Remaining unaccepted parameters: `{summary['remaining_unaccepted_parameter_count']}`",
        f"- Accepted full-circuit replay certificates: `{summary['accepted_full_circuit_replay_certificate_count']}`",
        f"- Accepted occurrence/proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Parameter Pressure Rows",
        "",
        "| Param index | Value/pi | Pi/4 error | Best dyadic pi grid | Dyadic error | Best rational pi grid | Rational error | Accepted |",
        "|---:|---:|---:|---|---:|---|---:|---|",
    ]
    for row in rows:
        dyadic = f"{row['best_power_of_two_pi_numerator']}/{row['best_power_of_two_pi_denominator']}"
        rational = f"{row['best_rational_pi_numerator']}/{row['best_rational_pi_denominator']}"
        lines.append(
            f"| {row['parameter_index']} | {row['value_over_pi']:.12f} | "
            f"{row['nearest_pi_over_four_error']:.6e} | {dyadic} | "
            f"{row['best_power_of_two_pi_error']:.6e} | {rational} | "
            f"{row['best_rational_pi_error']:.6e} | "
            f"{row['accepted_exact_decomposition']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This closes only a simple exact-decomposition route. It does not prove that line 1381 cannot be solved by a broader symbolic synthesis, context-aware absorption, or a verified full-circuit replay. The B7 ledger remains unchanged at zero accepted occurrence removals and zero accepted proxy-T reduction.",
            "",
            "## Next Required Gate",
            "",
            "The next B1/B7 route must leave the local parameter-only setting: either construct a broader symbolic synthesis object for line 1381, absorb the five parameters into neighboring context with replay certificates, or produce a full-circuit replay certificate that prices the remaining rotations honestly.",
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
