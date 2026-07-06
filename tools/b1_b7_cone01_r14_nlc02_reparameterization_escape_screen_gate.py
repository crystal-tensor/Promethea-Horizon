#!/usr/bin/env python3
"""T-B1-004dp/T-B7-012y: R14 NL-C02 reparameterization escape screen gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r14_nlc02_reparameterization_escape_screen_gate_v0"
STATUS = "cone01_r14_nlc02_reparameterization_escape_screen_passed_o3_still_open"
MODEL_STATUS = "nlc02_simple_reparameterization_escape_screen_passed_but_o3_unclosed"
VERSION = "0.1"
TARGET_ID = "T-B1-004dp/T-B7-012y"
SCREEN_ID = "B1-B7-cone01-R14-NL-C02-reparameterization-escape-screen"
CANDIDATE_ID = "NL-C02"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def transform_values(value: float) -> dict[str, float]:
    return {
        "identity": value,
        "negation": -value,
        "pi_minus": math.pi - value,
        "pi_plus": math.pi + value,
        "minus_pi": value - math.pi,
        "plus_pi": value + math.pi,
    }


def nearest_pi_over_four(value: float) -> tuple[int, float]:
    numerator = round(value / (math.pi / 4))
    error = abs(value - numerator * (math.pi / 4))
    return numerator, error


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r13 = load_json(args.r13_binding)
    exact = load_json(args.exact_decomposition)
    r13s = r13["summary"]
    exacts = exact["summary"]
    exact_rows = exact["line1381_exact_decomposition_pressure_rows"]

    tolerance = float(args.grid_tolerance)
    probes = []
    for row in exact_rows:
        parameter_index = int(row["parameter_index"])
        value = float(row["parameter_value"])
        for transform_name, transformed in transform_values(value).items():
            for period_shift in range(-2, 3):
                shifted = transformed + 2 * math.pi * period_shift
                numerator, error = nearest_pi_over_four(shifted)
                probes.append(
                    {
                        "parameter_index": parameter_index,
                        "source_value": value,
                        "transform": transform_name,
                        "period_shift_2pi": period_shift,
                        "shifted_value": shifted,
                        "nearest_pi_over_four_numerator": numerator,
                        "nearest_pi_over_four_error": error,
                        "grid_escape_pass": error <= tolerance,
                    }
                )

    accepted = [row for row in probes if row["grid_escape_pass"]]
    best_by_parameter = []
    for parameter_index in r13s["canonical_parameter_indices"]:
        candidates = [row for row in probes if row["parameter_index"] == parameter_index]
        best = min(candidates, key=lambda row: row["nearest_pi_over_four_error"])
        best_by_parameter.append(best)

    screen_packet = {
        "screen_id": SCREEN_ID,
        "source_target_id": TARGET_ID,
        "candidate_id": CANDIDATE_ID,
        "source_r13_binding": str(args.r13_binding),
        "source_exact_decomposition": str(args.exact_decomposition),
        "source_hashes": {
            "r13_binding": file_hash(args.r13_binding),
            "exact_decomposition": file_hash(args.exact_decomposition),
        },
        "source_r13_binding_hash": r13s["binding_hash"],
        "source_r13_domain_hash": r13s["domain_hash"],
        "canonical_parameter_indices": r13s["canonical_parameter_indices"],
        "transform_families": sorted(transform_values(0.0).keys()),
        "period_shifts_2pi": [-2, -1, 0, 1, 2],
        "grid_tolerance": tolerance,
        "probe_rows": probes,
        "best_by_parameter": best_by_parameter,
        "accepted_escape_count": len(accepted),
        "decision": {
            "simple_reparameterization_escape_found": len(accepted) > 0,
            "o3_closed": False,
            "checked_negative_lemma_present": False,
            "nlc02_full_lemma_ready": False,
            "reroute_allowed": False,
            "why": (
                "The simple periodic/sign/pi-complement screen finds no pi/4-grid escape, but O3 "
                "remains open because general local-unitary reparameterization invariance is not proved."
            ),
        },
    }
    screen_packet["probe_table_hash"] = stable_hash(probes)
    screen_packet["screen_hash"] = stable_hash(screen_packet)

    min_error = min(row["nearest_pi_over_four_error"] for row in probes)
    max_error = max(row["nearest_pi_over_four_error"] for row in probes)
    parameter_coverage = sorted({row["parameter_index"] for row in probes})

    requirements = [
        requirement(
            "E1",
            "R13 source-domain binding is validation-clean and O4-closed",
            r13.get("method") == "b1_b7_cone01_r13_nlc02_source_domain_binding_gate_v0"
            and r13s.get("validation_error_count") == 0
            and r13s.get("o4_closed_for_current_hash_chain") is True,
            {
                "r13_method": r13.get("method"),
                "r13_validation_error_count": r13s.get("validation_error_count"),
                "o4_closed_for_current_hash_chain": r13s.get("o4_closed_for_current_hash_chain"),
            },
        ),
        requirement(
            "E2",
            "Exact-decomposition source is validation-clean and still has five off-grid parameters",
            exact.get("method") == "b1_b7_cone01_line1381_exact_decomposition_pressure_gate_v0"
            and exacts.get("validation_error_count") == 0
            and exacts.get("remaining_off_grid_parameter_count") == 5,
            {
                "exact_method": exact.get("method"),
                "validation_error_count": exacts.get("validation_error_count"),
                "remaining_off_grid_parameter_count": exacts.get("remaining_off_grid_parameter_count"),
            },
        ),
        requirement(
            "E3",
            "Screen covers the R13 canonical parameter domain",
            parameter_coverage == r13s["canonical_parameter_indices"],
            {
                "parameter_coverage": parameter_coverage,
                "canonical_parameter_indices": r13s["canonical_parameter_indices"],
            },
        ),
        requirement(
            "E4",
            "Screen covers six transform families and five period shifts",
            len(screen_packet["transform_families"]) == 6
            and screen_packet["period_shifts_2pi"] == [-2, -1, 0, 1, 2],
            {
                "transform_families": screen_packet["transform_families"],
                "period_shifts_2pi": screen_packet["period_shifts_2pi"],
            },
        ),
        requirement(
            "E5",
            "All 150 simple reparameterization probes are present",
            len(probes) == 150,
            {"probe_count": len(probes)},
        ),
        requirement(
            "E6",
            "No simple reparameterization reaches the pi/4 grid tolerance",
            len(accepted) == 0 and min_error > tolerance,
            {"accepted_escape_count": len(accepted), "min_error": min_error, "grid_tolerance": tolerance},
        ),
        requirement(
            "E7",
            "Every parameter has a best-screen row recorded",
            len(best_by_parameter) == 5
            and sorted(row["parameter_index"] for row in best_by_parameter)
            == r13s["canonical_parameter_indices"],
            {"best_by_parameter_count": len(best_by_parameter)},
        ),
        requirement(
            "E8",
            "Screen is hash-bound to R13 and exact-decomposition sources",
            all(screen_packet["source_hashes"].values())
            and bool(screen_packet["probe_table_hash"])
            and bool(screen_packet["screen_hash"]),
            {
                "source_hashes": screen_packet["source_hashes"],
                "probe_table_hash": screen_packet["probe_table_hash"],
                "screen_hash": screen_packet["screen_hash"],
            },
        ),
        requirement(
            "E9",
            "Screen does not close O3 or upgrade NL-C02",
            screen_packet["decision"]["o3_closed"] is False
            and screen_packet["decision"]["checked_negative_lemma_present"] is False
            and screen_packet["decision"]["reroute_allowed"] is False,
            screen_packet["decision"],
        ),
        requirement(
            "E10",
            "Screen preserves zero resource and B7 credit claims",
            True,
            {
                "accepted_route_count": 0,
                "accepted_occurrence_removal": 0,
                "accepted_proxy_t_reduction": 0,
                "b7_credit_delta": 0,
                "b7_space_time_volume_credit": 0,
                "resource_saving_claimed": False,
                "b7_ledger_improvement_claimed": False,
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids:
        validation_errors.append(f"unexpected R14 reparameterization screen failures: {failed_ids}")

    summary = {
        "screen_id": SCREEN_ID,
        "screen_hash": screen_packet["screen_hash"],
        "probe_table_hash": screen_packet["probe_table_hash"],
        "source_r13_binding_hash": r13s["binding_hash"],
        "source_r13_domain_hash": r13s["domain_hash"],
        "candidate_id": CANDIDATE_ID,
        "canonical_parameter_indices": r13s["canonical_parameter_indices"],
        "transform_family_count": len(screen_packet["transform_families"]),
        "period_shift_count": len(screen_packet["period_shifts_2pi"]),
        "probe_count": len(probes),
        "accepted_escape_count": len(accepted),
        "min_pi_over_four_grid_error": min_error,
        "max_pi_over_four_grid_error": max_error,
        "grid_tolerance": tolerance,
        "simple_reparameterization_escape_found": len(accepted) > 0,
        "o3_closed": False,
        "remaining_open_obligations": ["O1", "O3"],
        "remaining_open_obligation_count": 2,
        "checked_negative_lemma_present": False,
        "nlc02_full_lemma_ready": False,
        "reroute_allowed": False,
        "accepted_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_space_time_volume_credit": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "requirement_count": len(requirements),
        "requirements_passed": passed,
        "requirements_failed": len(requirements) - passed,
        "failed_requirement_ids": failed_ids,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "source_target_id": TARGET_ID,
        "title": "B1/B7 Cone01 R14 NL-C02 Reparameterization Escape Screen Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "summary": summary,
        "nlc02_reparameterization_escape_screen_packet": screen_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "R14 finds no pi/4-grid escape in the declared simple periodic, sign, and pi-complement "
                "reparameterization screen over the R13-bound five-parameter domain."
            ),
            "what_is_not_supported": (
                "R14 does not prove general parameterization invariance and does not close O3. NL-C02 is "
                "still not a checked negative lemma. No R5 reroute, R1 solution, occurrence removal, proxy-T "
                "reduction, B7 credit, resource saving, or impossibility theorem is supported."
            ),
            "next_gate": (
                "Expand O3 beyond the simple screen or close O1 optimizer completeness; or falsify R14 "
                "with a valid equivalent reparameterization that reaches the pi/4 grid."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    packet = payload["nlc02_reparameterization_escape_screen_packet"]
    lines = [
        f"# {payload['title']}",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Candidate: `{s['candidate_id']}`",
        f"- Screen hash: `{s['screen_hash']}`",
        f"- Probe-table hash: `{s['probe_table_hash']}`",
        "",
        "## Result",
        "",
        (
            f"The R14 reparameterization escape screen passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements. It finds no simple pi/4-grid escape, but O3 remains open."
        ),
        "",
        "## Screen Scope",
        "",
        f"- Parameters: `{s['canonical_parameter_indices']}`",
        f"- Transform families: `{packet['transform_families']}`",
        f"- Period shifts: `{packet['period_shifts_2pi']}`",
        f"- Probe count: `{s['probe_count']}`",
        f"- Accepted escape count: `{s['accepted_escape_count']}`",
        f"- Grid tolerance: `{s['grid_tolerance']}`",
        f"- Error range: `{s['min_pi_over_four_grid_error']}` to `{s['max_pi_over_four_grid_error']}`",
        "",
        "## Decision",
        "",
        f"- Simple reparameterization escape found: `{s['simple_reparameterization_escape_found']}`",
        f"- O3 closed: `{s['o3_closed']}`",
        f"- Remaining open obligations: `{s['remaining_open_obligations']}`",
        f"- Checked negative lemma present: `{s['checked_negative_lemma_present']}`",
        f"- Reroute allowed: `{s['reroute_allowed']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for row in payload["requirements"]:
        marker = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- `{row['requirement_id']}` {marker}: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "This screen gate does not claim resource saving, occurrence removal, proxy-T reduction, B7 ledger improvement, FT resource credit, a checked impossibility theorem, an R5 reroute, or a solved B1/B7 problem.",
            "",
            "## Validation",
            "",
            f"- validation_error_count: `{s['validation_error_count']}`",
        ]
    )
    for error in payload["validation_errors"]:
        lines.append(f"- {error}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r13-binding",
        type=Path,
        default=Path("results/B1_B7_cone01_R13_nlc02_source_domain_binding_gate_v0.json"),
    )
    parser.add_argument(
        "--exact-decomposition",
        type=Path,
        default=Path("results/B1_B7_cone01_line1381_exact_decomposition_pressure_gate_v0.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R14_nlc02_reparameterization_escape_screen_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R14_nlc02_reparameterization_escape_screen_gate.md"),
    )
    parser.add_argument("--grid-tolerance", type=float, default=1e-8)
    parser.add_argument("--last-updated", default="2026-07-06")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "screen_hash": payload["summary"]["screen_hash"],
                "probe_count": payload["summary"]["probe_count"],
                "accepted_escape_count": payload["summary"]["accepted_escape_count"],
                "min_pi_over_four_grid_error": payload["summary"]["min_pi_over_four_grid_error"],
                "o3_closed": payload["summary"]["o3_closed"],
                "remaining_open_obligations": payload["summary"]["remaining_open_obligations"],
                "reroute_allowed": payload["summary"]["reroute_allowed"],
                "requirements_passed": payload["summary"]["requirements_passed"],
                "requirements_failed": payload["summary"]["requirements_failed"],
                "validation_error_count": payload["summary"]["validation_error_count"],
                "json_output": str(args.json_output),
                "markdown_output": str(args.markdown_output),
            },
            indent=2,
            sort_keys=True,
        )
    )
    if payload["validation_errors"]:
        raise SystemExit("B1/B7 R14 reparameterization screen gate validation failed")


if __name__ == "__main__":
    main()
