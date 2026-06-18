#!/usr/bin/env python3
"""Factory-amortization scaffold for B1/B7 cone_01 shared-theta objects.

This gate asks whether the replayed and logically routed shared-theta objects
have enough reuse structure to support a factory-amortization ledger.  It
counts baseline per-occurrence synthesis pressure, shared per-object synthesis
pressure, and the resulting gross proxy-T pressure difference.

The gate deliberately does not accept a physical cost model.  It has no
synthesis-error budget, no independent physical baseline, and no refreshed B7
ledger.  It is CM-05 scaffold evidence only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_shared_theta_factory_amortization_gate_v0"
STATUS = "cone01_shared_theta_factory_amortization_scaffold"
MODEL_STATUS = "factory_amortization_scaffold_not_physical_cost_model"
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
    theta_gate = read_json(args.theta_sharing_gate)
    layout_gate = read_json(args.layout_routing_gate)
    theta_summary = theta_gate["summary"]
    layout_summary = layout_gate["summary"]
    layout_rows = layout_gate["layout_route_rows"]

    object_rows = []
    baseline_compilation_count = 0
    shared_compilation_count = 0
    amortized_saved_compilation_count = 0
    for row in layout_rows:
        occurrences = int(row["route_packet_count"])
        shared_compile_count = 1
        saved = max(0, occurrences - shared_compile_count)
        baseline_compilation_count += occurrences
        shared_compilation_count += shared_compile_count
        amortized_saved_compilation_count += saved
        object_rows.append(
            {
                "object_id": row["object_id"],
                "canonical_theta": row["canonical_theta"],
                "occurrence_count": occurrences,
                "shared_object_compile_count": shared_compile_count,
                "amortized_saved_compile_count": saved,
                "baseline_proxy_t_pressure": occurrences * PROXY_T_COST_PER_ARBITRARY_ROTATION,
                "shared_object_proxy_t_pressure": shared_compile_count * PROXY_T_COST_PER_ARBITRARY_ROTATION,
                "gross_proxy_t_pressure_delta": saved * PROXY_T_COST_PER_ARBITRARY_ROTATION,
                "logical_anchor_qubit": row["logical_anchor_qubit"],
                "total_logical_hop_count": row["total_logical_hop_count"],
                "max_logical_hop_count": row["max_logical_hop_count"],
                "factory_amortization_evidence_present": True,
                "physical_factory_schedule_present": False,
                "shared_error_budget_present": False,
            }
        )

    baseline_proxy_t_pressure = baseline_compilation_count * PROXY_T_COST_PER_ARBITRARY_ROTATION
    shared_object_proxy_t_pressure = shared_compilation_count * PROXY_T_COST_PER_ARBITRARY_ROTATION
    gross_proxy_t_pressure_delta = baseline_proxy_t_pressure - shared_object_proxy_t_pressure
    factory_gate_passed = (
        layout_summary["layout_routing_gate_passed"] is True
        and baseline_compilation_count == int(theta_summary["candidate_window_count"])
        and shared_compilation_count == int(theta_summary["distinct_theta_group_count"])
        and amortized_saved_compilation_count == int(theta_summary["duplicate_theta_occurrence_count"])
        and gross_proxy_t_pressure_delta == int(theta_summary["optimistic_cache_proxy_t_reuse"])
    )

    payload = {
        "benchmark_id": "B1",
        "problem_id": 25,
        "linked_b7_problem_id": 21,
        "title": "B1/B7 cone_01 shared-theta factory-amortization scaffold",
        "version": VERSION,
        "last_updated": args.last_updated,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "method": METHOD,
        "source_theta_sharing_ledger_gate": display_path(args.theta_sharing_gate),
        "source_shared_theta_layout_routing_gate": display_path(args.layout_routing_gate),
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "summary": {
            "candidate_window_count": int(theta_summary["candidate_window_count"]),
            "shared_synthesis_object_count": int(layout_summary["shared_synthesis_object_count"]),
            "layout_routed_occurrence_count": int(layout_summary["layout_routed_occurrence_count"]),
            "distinct_theta_group_count": int(theta_summary["distinct_theta_group_count"]),
            "duplicate_theta_occurrence_count": int(theta_summary["duplicate_theta_occurrence_count"]),
            "proxy_t_cost_per_arbitrary_rotation": PROXY_T_COST_PER_ARBITRARY_ROTATION,
            "baseline_factory_compilation_count": baseline_compilation_count,
            "shared_object_factory_compilation_count": shared_compilation_count,
            "amortized_saved_compilation_count": amortized_saved_compilation_count,
            "baseline_proxy_t_pressure": baseline_proxy_t_pressure,
            "shared_object_proxy_t_pressure": shared_object_proxy_t_pressure,
            "gross_proxy_t_pressure_delta": gross_proxy_t_pressure_delta,
            "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": int(
                theta_summary["target_proxy_t_ledger_reduction_for_gcm_h6_1_20"]
            ),
            "factory_amortization_gate_passed": factory_gate_passed,
            "physical_factory_schedule_present": False,
            "shared_error_budget_present": False,
            "independent_baseline_present": False,
            "refreshed_b7_ledger_present": False,
            "occurrence_ledger_removed_occurrences": 0,
            "occurrence_ledger_proxy_t_reduction": 0,
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "validation_error_count": None,
        },
        "object_amortization_rows": object_rows,
        "claim_boundary": {
            "cost_model_accepted": False,
            "rewrite_claimed": False,
            "resource_saving_claimed": False,
            "semantic_certificate_claimed": False,
            "physical_resource_reduction_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "supported_claim": (
                "The replayed and logically routed shared-theta objects have explicit "
                "factory-amortization bookkeeping: 35 baseline per-occurrence synthesis "
                "requests collapse to 4 shared-object synthesis requests in the scaffold."
            ),
            "unsupported_claims": [
                "No physical factory schedule is supplied.",
                "No synthesis-error or correlation budget is supplied.",
                "No independent physical baseline validates the amortization model.",
                "No B7 ledger reduction is counted.",
            ],
            "next_gate": (
                "Use this as CM-05 factory-amortization scaffold evidence, then build "
                "CM-06 shared-error budget and CM-07 independent-baseline evidence before "
                "any physical theta-sharing cost model can be accepted."
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
    if payload.get("method") != METHOD:
        errors.append("method mismatch")
    if payload.get("status") != STATUS:
        errors.append("status mismatch")
    if payload.get("model_status") != MODEL_STATUS:
        errors.append("model_status mismatch")
    expected = {
        "candidate_window_count": 35,
        "shared_synthesis_object_count": 4,
        "layout_routed_occurrence_count": 35,
        "distinct_theta_group_count": 4,
        "duplicate_theta_occurrence_count": 31,
        "baseline_factory_compilation_count": 35,
        "shared_object_factory_compilation_count": 4,
        "amortized_saved_compilation_count": 31,
        "baseline_proxy_t_pressure": 700,
        "shared_object_proxy_t_pressure": 80,
        "gross_proxy_t_pressure_delta": 620,
        "target_proxy_t_ledger_reduction_for_gcm_h6_1_20": 600,
    }
    for field, value in expected.items():
        if summary.get(field) != value:
            errors.append(f"{field} expected {value}")
    if summary.get("factory_amortization_gate_passed") is not True:
        errors.append("factory amortization scaffold should pass")
    for field in [
        "physical_factory_schedule_present",
        "shared_error_budget_present",
        "independent_baseline_present",
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
    if summary.get("occurrence_ledger_removed_occurrences") != 0:
        errors.append("occurrence removals must remain zero")
    if summary.get("occurrence_ledger_proxy_t_reduction") != 0:
        errors.append("occurrence proxy-T reduction must remain zero")
    for row in payload["object_amortization_rows"]:
        if row.get("factory_amortization_evidence_present") is not True:
            errors.append(f"{row.get('object_id')} missing amortization evidence")
        if row.get("physical_factory_schedule_present") is not False:
            errors.append(f"{row.get('object_id')} must not claim a physical factory schedule")
        if row.get("shared_error_budget_present") is not False:
            errors.append(f"{row.get('object_id')} must not claim an error budget")
    return errors


def markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone_01 Shared-Theta Factory-Amortization Scaffold",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This artifact adds CM-05 bookkeeping for the replayed and logically routed "
        "shared-theta objects. It compares per-occurrence synthesis pressure against "
        "per-shared-object synthesis pressure.",
        "",
        "It is not a physical factory schedule, not an error-budget model, not a "
        "semantic rewrite certificate, and not a B7 resource-saving claim.",
        "",
        "## Summary",
        "",
        f"- Candidate windows: `{summary['candidate_window_count']}`",
        f"- Shared objects: `{summary['shared_synthesis_object_count']}`",
        f"- Baseline factory compilation count: `{summary['baseline_factory_compilation_count']}`",
        f"- Shared-object factory compilation count: `{summary['shared_object_factory_compilation_count']}`",
        f"- Amortized saved compilation count: `{summary['amortized_saved_compilation_count']}`",
        f"- Baseline proxy-T pressure: `{summary['baseline_proxy_t_pressure']}`",
        f"- Shared-object proxy-T pressure: `{summary['shared_object_proxy_t_pressure']}`",
        f"- Gross proxy-T pressure delta: `{summary['gross_proxy_t_pressure_delta']}`",
        f"- Target proxy-T ledger reduction: `{summary['target_proxy_t_ledger_reduction_for_gcm_h6_1_20']}`",
        f"- Factory amortization gate passed: `{summary['factory_amortization_gate_passed']}`",
        f"- Physical factory schedule present: `{summary['physical_factory_schedule_present']}`",
        f"- Shared error budget present: `{summary['shared_error_budget_present']}`",
        f"- Cost model accepted: `{summary['cost_model_accepted']}`",
        f"- B7 ledger improvement claimed: `{summary['b7_ledger_improvement_claimed']}`",
        f"- Validation errors: `{summary['validation_error_count']}`",
        "",
        "## Object Amortization",
        "",
        "| object | occurrences | shared compiles | saved compiles | gross proxy-T delta | total hops | max hops |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["object_amortization_rows"]:
        lines.append(
            f"| {row['object_id']} | `{row['occurrence_count']}` | `{row['shared_object_compile_count']}` | "
            f"`{row['amortized_saved_compile_count']}` | `{row['gross_proxy_t_pressure_delta']}` | "
            f"`{row['total_logical_hop_count']}` | `{row['max_logical_hop_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The factory-amortization scaffold is strong enough to keep CM-05 open as "
            "positive bookkeeping evidence: the same four theta groups account for 31 "
            "amortized compile requests and a gross 620 proxy-T pressure difference. "
            "It is still not accepted as B7 savings because the project has no shared "
            "synthesis-error budget, no independent physical baseline, and no refreshed "
            "B7 ledger.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--theta-sharing-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_theta_sharing_ledger_gate_v0.json",
    )
    parser.add_argument(
        "--layout-routing-gate",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_layout_routing_gate_v0.json",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "results" / "B1_B7_cone01_shared_theta_factory_amortization_gate_v0.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "research" / "B1_B7_cone01_shared_theta_factory_amortization_gate.md",
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
