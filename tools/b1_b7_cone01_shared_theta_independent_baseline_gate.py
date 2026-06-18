#!/usr/bin/env python3
"""Independent-baseline scaffold for B1/B7 cone_01 shared-theta accounting.

This gate checks whether the shared-theta cache signal is being double-counted
as an occurrence-level saving. It compares a baseline per-occurrence synthesis
ledger with the shared-object synthesis ledger, then confirms that none of the
gross cache/amortization signal has been promoted into the accepted occurrence
ledger.

The gate deliberately does not accept a physical cost model. It is an
independent accounting baseline, not a physical device baseline, not a refreshed
B7 ledger, and not a resource-saving claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_shared_theta_independent_baseline_gate_v0"
STATUS = "cone01_shared_theta_independent_baseline_scaffold"
MODEL_STATUS = "independent_baseline_scaffold_not_physical_cost_model"
VERSION = "0.1"
PROXY_T_COST_PER_ARBITRARY_ROTATION = 20


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def display_path(path: Path) -> str:
    root = Path(__file__).resolve().parents[1]
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(root))
    except ValueError:
        return str(path)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    error_budget_gate = read_json(args.error_budget_gate)
    factory_gate = read_json(args.factory_amortization_gate)
    theta_gate = read_json(args.theta_sharing_gate)
    error_summary = error_budget_gate["summary"]
    factory_summary = factory_gate["summary"]
    theta_summary = theta_gate["summary"]

    factory_rows = {
        row["object_id"]: row
        for row in factory_gate["object_amortization_rows"]
    }
    error_rows = error_budget_gate["object_error_budget_rows"]
    baseline_rows = []
    total_baseline_proxy_t = 0
    total_shared_proxy_t = 0
    total_gross_delta = 0
    total_double_counted_occurrences = 0
    total_double_counted_proxy_t = 0
    for row in error_rows:
        object_id = row["object_id"]
        factory_row = factory_rows[object_id]
        baseline_occurrences = int(row["occurrence_count"])
        shared_objects = 1
        baseline_proxy_t = baseline_occurrences * PROXY_T_COST_PER_ARBITRARY_ROTATION
        shared_proxy_t = shared_objects * PROXY_T_COST_PER_ARBITRARY_ROTATION
        gross_delta = baseline_proxy_t - shared_proxy_t
        occurrence_ledger_removed_occurrences = 0
        occurrence_ledger_proxy_t_reduction = 0
        double_counted_occurrences = occurrence_ledger_removed_occurrences
        double_counted_proxy_t = occurrence_ledger_proxy_t_reduction
        total_baseline_proxy_t += baseline_proxy_t
        total_shared_proxy_t += shared_proxy_t
        total_gross_delta += gross_delta
        total_double_counted_occurrences += double_counted_occurrences
        total_double_counted_proxy_t += double_counted_proxy_t
        baseline_rows.append(
            {
                "object_id": object_id,
                "canonical_theta": row["canonical_theta"],
                "baseline_occurrence_count": baseline_occurrences,
                "shared_object_count": shared_objects,
                "duplicate_occurrence_count": int(factory_row["amortized_saved_compile_count"]),
                "baseline_proxy_t_pressure": baseline_proxy_t,
                "shared_object_proxy_t_pressure": shared_proxy_t,
                "gross_proxy_t_pressure_delta": gross_delta,
                "occurrence_ledger_removed_occurrences": occurrence_ledger_removed_occurrences,
                "occurrence_ledger_proxy_t_reduction": occurrence_ledger_proxy_t_reduction,
                "double_counted_occurrence_count": double_counted_occurrences,
                "double_counted_proxy_t_pressure": double_counted_proxy_t,
                "cache_label_count": shared_objects,
                "cache_label_promoted_to_occurrence_saving": False,
                "independent_accounting_baseline_present": True,
                "independent_physical_baseline_present": False,
                "device_calibrated_baseline_present": False,
            }
        )

    independent_baseline_gate_passed = (
        error_summary["shared_error_budget_gate_passed"] is True
        and int(error_summary["candidate_window_count"]) == int(theta_summary["candidate_window_count"])
        and int(error_summary["shared_synthesis_object_count"]) == int(theta_summary["distinct_theta_group_count"])
        and total_baseline_proxy_t == 700
        and total_shared_proxy_t == 80
        and total_gross_delta == int(theta_summary["optimistic_cache_proxy_t_reuse"])
        and total_double_counted_occurrences == 0
        and total_double_counted_proxy_t == 0
        and int(theta_summary["occurrence_ledger_removed_occurrences"]) == 0
        and int(theta_summary["occurrence_ledger_proxy_t_reduction"]) == 0
    )

    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 shared-theta independent-baseline scaffold",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_shared_theta_error_budget_gate": display_path(args.error_budget_gate),
        "source_shared_theta_factory_amortization_gate": display_path(args.factory_amortization_gate),
        "source_theta_sharing_ledger_gate": display_path(args.theta_sharing_gate),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": {
            "candidate_window_count": int(theta_summary["candidate_window_count"]),
            "shared_synthesis_object_count": int(error_summary["shared_synthesis_object_count"]),
            "distinct_theta_group_count": int(theta_summary["distinct_theta_group_count"]),
            "duplicate_theta_occurrence_count": int(theta_summary["duplicate_theta_occurrence_count"]),
            "baseline_occurrence_count": int(theta_summary["candidate_window_count"]),
            "shared_object_count": int(error_summary["shared_synthesis_object_count"]),
            "proxy_t_cost_per_arbitrary_rotation": PROXY_T_COST_PER_ARBITRARY_ROTATION,
            "baseline_proxy_t_pressure": total_baseline_proxy_t,
            "shared_object_proxy_t_pressure": total_shared_proxy_t,
            "gross_proxy_t_pressure_delta": total_gross_delta,
            "occurrence_ledger_removed_occurrences": 0,
            "occurrence_ledger_proxy_t_reduction": 0,
            "double_counted_occurrence_count": total_double_counted_occurrences,
            "double_counted_proxy_t_pressure": total_double_counted_proxy_t,
            "cache_label_count": len(baseline_rows),
            "independent_baseline_gate_passed": independent_baseline_gate_passed,
            "independent_baseline_present": True,
            "independent_physical_baseline_present": False,
            "device_calibrated_baseline_present": False,
            "refreshed_b7_ledger_present": False,
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "validation_error_count": None,
        },
        "independent_baseline_rows": baseline_rows,
        "claim_boundary": {
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The scaffold now includes an independent accounting baseline showing "
                "that the 620 gross proxy-T cache/amortization signal is not double-counted "
                "as accepted occurrence-ledger savings."
            ),
            "unsupported_claims": [
                "No independent physical device baseline is supplied.",
                "No device-calibrated baseline validates the shared-theta model.",
                "No occurrence-removing semantic certificate is produced.",
                "No refreshed B7 ledger accepts the gross cache signal as a resource saving.",
            ],
            "next_gate": (
                "Use this as CM-07 independent-baseline scaffold evidence, then build "
                "CM-08 refreshed-B7-ledger evidence before any physical theta-sharing "
                "cost model can be accepted."
            ),
        },
    }
    errors = validate(payload)
    payload["summary"]["validation_error_count"] = len(errors)
    payload["validation_errors"] = errors
    return payload


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    expected = {
        "candidate_window_count": 35,
        "shared_synthesis_object_count": 4,
        "distinct_theta_group_count": 4,
        "duplicate_theta_occurrence_count": 31,
        "baseline_occurrence_count": 35,
        "shared_object_count": 4,
        "baseline_proxy_t_pressure": 700,
        "shared_object_proxy_t_pressure": 80,
        "gross_proxy_t_pressure_delta": 620,
        "occurrence_ledger_removed_occurrences": 0,
        "occurrence_ledger_proxy_t_reduction": 0,
        "double_counted_occurrence_count": 0,
        "double_counted_proxy_t_pressure": 0,
        "cache_label_count": 4,
    }
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field} expected {value}")
    if summary.get("independent_baseline_gate_passed") is not True:
        errors.append("independent-baseline scaffold should pass")
    for field in [
        "independent_physical_baseline_present",
        "device_calibrated_baseline_present",
        "refreshed_b7_ledger_present",
        "cost_model_accepted",
        "rewrite_claimed",
        "resource_saving_claimed",
        "semantic_certificate_claimed",
        "physical_resource_reduction_claimed",
        "b7_ledger_improvement_claimed",
    ]:
        if summary.get(field) is not False:
            errors.append(f"{field} must remain false in summary")
        if field in claims and claims.get(field) is not False:
            errors.append(f"{field} must remain false in claim boundary")
    for row in payload["independent_baseline_rows"]:
        if row.get("cache_label_promoted_to_occurrence_saving") is not False:
            errors.append(f"{row.get('object_id')} must not promote cache label to occurrence saving")
        if row.get("independent_accounting_baseline_present") is not True:
            errors.append(f"{row.get('object_id')} missing independent accounting baseline")
        if row.get("independent_physical_baseline_present") is not False:
            errors.append(f"{row.get('object_id')} must not claim independent physical baseline")
        if row.get("device_calibrated_baseline_present") is not False:
            errors.append(f"{row.get('object_id')} must not claim device-calibrated baseline")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Shared-Theta Independent-Baseline Scaffold",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact adds CM-07 bookkeeping for the replayed, logically routed, "
        "factory-amortized, and error-budgeted shared-theta objects. It compares "
        "the baseline occurrence ledger with the shared-object ledger and confirms "
        "that the gross cache signal has not been double-counted as accepted "
        "occurrence-ledger savings.",
        "",
        "It is not an independent physical device baseline, not a semantic rewrite "
        "certificate, not a refreshed B7 ledger, and not a resource-saving claim.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Shared objects: `{summary['shared_synthesis_object_count']}`",
        f"- Baseline occurrences: `{summary['baseline_occurrence_count']}`",
        f"- Baseline/shared-object proxy-T pressure: `{summary['baseline_proxy_t_pressure']}` / `{summary['shared_object_proxy_t_pressure']}`",
        f"- Gross proxy-T pressure delta: `{summary['gross_proxy_t_pressure_delta']}`",
        f"- Occurrence-ledger removed occurrences: `{summary['occurrence_ledger_removed_occurrences']}`",
        f"- Occurrence-ledger proxy-T reduction: `{summary['occurrence_ledger_proxy_t_reduction']}`",
        f"- Double-counted occurrences / proxy-T: `{summary['double_counted_occurrence_count']}` / `{summary['double_counted_proxy_t_pressure']}`",
        f"- Independent baseline gate passed: `{summary['independent_baseline_gate_passed']}`",
        f"- Independent physical baseline present: `{summary['independent_physical_baseline_present']}`",
        f"- Device-calibrated baseline present: `{summary['device_calibrated_baseline_present']}`",
        f"- Refreshed B7 ledger present: `{summary['refreshed_b7_ledger_present']}`",
        f"- Cost model accepted: `{summary['cost_model_accepted']}`",
        f"- B7 ledger improvement claimed: `{summary['b7_ledger_improvement_claimed']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Independent Baseline Rows",
        "",
        "| object | baseline occurrences | shared objects | baseline proxy-T | shared proxy-T | gross delta | double-counted proxy-T |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["independent_baseline_rows"]:
        lines.append(
            f"| {row['object_id']} | {row['baseline_occurrence_count']} | "
            f"{row['shared_object_count']} | {row['baseline_proxy_t_pressure']} | "
            f"{row['shared_object_proxy_t_pressure']} | {row['gross_proxy_t_pressure_delta']} | "
            f"{row['double_counted_proxy_t_pressure']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This closes the CM-07 accounting-baseline gap only as a scaffold. The "
            "next cost-model blocker is CM-08: a refreshed B7 ledger that actually "
            "accepts the model and improves the gcm_h6 minimum row. Until that "
            "exists, the accepted B7 ledger reduction remains zero.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--error-budget-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_error_budget_gate_v0.json",
    )
    parser.add_argument(
        "--factory-amortization-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_factory_amortization_gate_v0.json",
    )
    parser.add_argument(
        "--theta-sharing-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_theta_sharing_ledger_gate_v0.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_independent_baseline_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "research" / "B1_B7_cone01_shared_theta_independent_baseline_gate.md",
    )
    parser.add_argument("--last-updated", default="2026-06-18")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_text(args.markdown_output, markdown(payload))
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Wrote {args.json_output}")
        print(f"Wrote {args.markdown_output}")


if __name__ == "__main__":
    main()
