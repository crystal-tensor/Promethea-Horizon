#!/usr/bin/env python3
"""T-B1-004cr/T-B7-010 route-triage decision gate for cone_01.

This gate consumes the latest line-1381 context, commutation-corridor,
seeded-replay resource-boundary, and shared-theta ledger artifacts. It does
not create a new rewrite. It records which current shortcut routes are closed
for B7 credit and what the next non-shortcut route must provide.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path


METHOD = "b1_b7_cone01_route_triage_decision_gate_v0"
STATUS = "cone01_route_triage_rejects_current_shortcuts_no_b7_credit"
MODEL_STATUS = "decision_gate_over_existing_b1_b7_evidence_not_rewrite"


DEFAULT_SOURCES = {
    "line1381_five_rotation_context": Path(
        "results/B1_B7_cone01_line1381_five_rotation_context_gate_v0.json"
    ),
    "line1381_commutation_corridor": Path(
        "results/B1_B7_cone01_line1381_commutation_corridor_gate_v0.json"
    ),
    "qiskit_loader_seeded_resource_boundary": Path(
        "results/B1_B7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate_v0.json"
    ),
    "theta_sharing_cost_model": Path("results/B1_B7_cone01_theta_sharing_cost_model_gate_v0.json"),
    "shared_theta_refreshed_b7_ledger": Path(
        "results/B1_B7_cone01_shared_theta_refreshed_b7_ledger_gate_v0.json"
    ),
    "line1381_all_grid_removal": Path(
        "results/B1_B7_cone01_line1381_leave_five_out_parameter_gate_v0.json"
    ),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def build(source_paths: dict[str, Path]) -> dict:
    sources = {name: load(path) for name, path in source_paths.items()}
    five_context = sources["line1381_five_rotation_context"]["summary"]
    corridor = sources["line1381_commutation_corridor"]["summary"]
    seeded = sources["qiskit_loader_seeded_resource_boundary"]["summary"]
    theta_cost = sources["theta_sharing_cost_model"]["summary"]
    refreshed = sources["shared_theta_refreshed_b7_ledger"]["summary"]
    all_grid = sources["line1381_all_grid_removal"]["summary"]

    route_rows = [
        {
            "route_id": "R1_seeded_semantic_replay",
            "source_method": sources["qiskit_loader_seeded_resource_boundary"]["method"],
            "positive_signal": "16 seeded product-state replay cases pass with high fidelity",
            "blocking_metric": "resource_boundary_failed_blocker_count",
            "blocking_value": seeded["resource_boundary_failed_blocker_count"],
            "accepted_for_b7_credit": False,
            "reason": "semantic replay does not clear line-1381 pricing, line-1378 recovery, occurrence removal, or B7 ledger gates",
        },
        {
            "route_id": "R2_bounded_context_absorption",
            "source_method": sources["line1381_five_rotation_context"]["method"],
            "positive_signal": "bounded meet-in-the-middle context search is reproducible",
            "blocking_metric": "width5_exact_absorption_parameter_count",
            "blocking_value": five_context["width5_exact_absorption_parameter_count"],
            "accepted_for_b7_credit": False,
            "reason": "0/5 remaining line-1381 parameters have exact width-5 context absorption",
        },
        {
            "route_id": "R3_commutation_corridor_shortcut",
            "source_method": sources["line1381_commutation_corridor"]["method"],
            "positive_signal": "10 best context candidates and 32 references were inspected",
            "blocking_metric": "accepted_commutation_corridor_replay_candidate_count",
            "blocking_value": corridor["accepted_commutation_corridor_replay_candidate_count"],
            "accepted_for_b7_credit": False,
            "reason": "no cheap replay-safe commutation corridor is accepted",
        },
        {
            "route_id": "R4_shared_theta_cache_saving",
            "source_method": sources["theta_sharing_cost_model"]["method"],
            "positive_signal": "optimistic 620 proxy-T cache signal and 6/8 cost-model gates",
            "blocking_metric": "cost_model_accepted",
            "blocking_value": theta_cost["cost_model_accepted"],
            "accepted_for_b7_credit": False,
            "reason": "physical cost model remains unaccepted and refreshed B7 ledger rejects theta sharing",
        },
        {
            "route_id": "R5_all_grid_parameter_removal",
            "source_method": sources["line1381_all_grid_removal"]["method"],
            "positive_signal": "all-grid endpoint pressure test is reproducible",
            "blocking_metric": "leave_five_out_exact_pass_count",
            "blocking_value": all_grid["leave_five_out_exact_pass_count"],
            "accepted_for_b7_credit": False,
            "reason": "snapping all five off-grid parameters to the pi/4 grid fails exact replay",
        },
    ]

    accepted_route_count = sum(1 for row in route_rows if row["accepted_for_b7_credit"])
    rejected_route_count = len(route_rows) - accepted_route_count
    next_route_options = [
        "commutation_aware_full_circuit_replay_certificate",
        "honest_line1381_local_u3_pricing_with_physical_synthesis_model",
        "line1378_recovery_without_overlap_double_counting",
        "alternate_occurrence_removing_scaffold",
    ]
    gate_results = {
        "G1_all_source_artifacts_present": all(path.exists() for path in source_paths.values()),
        "G2_no_current_shortcut_route_accepted_for_b7_credit": accepted_route_count == 0,
        "G3_seeded_replay_blockers_preserved": seeded["resource_boundary_failed_blocker_count"] == 5,
        "G4_context_and_corridor_routes_closed": (
            five_context["width5_exact_absorption_parameter_count"] == 0
            and corridor["accepted_commutation_corridor_replay_candidate_count"] == 0
        ),
        "G5_shared_theta_still_rejected_by_b7_ledger": (
            theta_cost["cost_model_accepted"] is False
            and refreshed["b7_ledger_accepts_theta_sharing"] is False
        ),
        "G6_no_resource_saving_claim": True,
    }
    validation_errors = []
    if not all(gate_results.values()):
        validation_errors.append("one or more route-triage consistency gates failed")

    return {
        "benchmark_id": "B1",
        "linked_b7_problem_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "source_methods": {name: payload["method"] for name, payload in sources.items()},
        "source_paths": {name: str(path) for name, path in source_paths.items()},
        "route_count": len(route_rows),
        "accepted_route_count": accepted_route_count,
        "rejected_route_count": rejected_route_count,
        "resource_boundary_failed_blocker_count": seeded["resource_boundary_failed_blocker_count"],
        "width5_exact_absorption_parameter_count": five_context[
            "width5_exact_absorption_parameter_count"
        ],
        "accepted_commutation_corridor_replay_candidate_count": corridor[
            "accepted_commutation_corridor_replay_candidate_count"
        ],
        "theta_cost_model_accepted": theta_cost["cost_model_accepted"],
        "refreshed_b7_ledger_accepts_theta_sharing": refreshed[
            "b7_ledger_accepts_theta_sharing"
        ],
        "optimistic_cache_proxy_t_reuse": theta_cost["optimistic_cache_proxy_t_reuse"],
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "recommended_next_route_count": len(next_route_options),
        "recommended_next_routes": next_route_options,
        "route_rows": route_rows,
        "acceptance_gate_count": len(gate_results),
        "passed_gate_count": sum(1 for passed in gate_results.values() if passed),
        "failed_gate_count": sum(1 for passed in gate_results.values() if not passed),
        "gate_results": gate_results,
        "validation_errors": validation_errors,
        "validation_error_count": len(validation_errors),
        "claim_boundary": {
            "supported_claim": (
                "The current seeded replay, bounded context, commutation corridor, "
                "shared-theta cache, and all-grid removal shortcuts do not produce B7 credit."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This is not a new circuit rewrite.",
                "This is not a full-circuit replay certificate.",
                "This does not prove a global lower bound for line 1381.",
                "This does not accept any occurrence removal or proxy-T reduction.",
            ],
        },
        "timestamp": time.time(),
    }


def render_markdown(payload: dict) -> str:
    rows = [
        "| Route | Blocking metric | Value | B7 credit |",
        "| --- | --- | ---: | --- |",
    ]
    for row in payload["route_rows"]:
        rows.append(
            f"| {row['route_id']} | {row['blocking_metric']} | {row['blocking_value']} | "
            f"{row['accepted_for_b7_credit']} |"
        )
    next_routes = "\n".join(f"- `{route}`" for route in payload["recommended_next_routes"])
    return "\n".join(
        [
            "# B1/B7 cone_01 Route Triage Decision Gate",
            "",
            "- Gate: T-B1-004cr / T-B7-010",
            f"- Method: `{payload['method']}`",
            f"- Status: `{payload['status']}`",
            f"- Routes triaged: {payload['route_count']}",
            f"- Routes accepted for B7 credit: {payload['accepted_route_count']}",
            f"- Gates passed: {payload['passed_gate_count']} / {payload['acceptance_gate_count']}",
            "",
            "## Route Table",
            "",
            *rows,
            "",
            "## Next Route Options",
            "",
            next_routes,
            "",
            "## Claim Boundary",
            "",
            "- This is a decision gate over existing evidence, not a new rewrite.",
            "- It does not prove a global lower bound or symbolic obstruction.",
            "- It does not accept occurrence removal, proxy-T reduction, or B7 ledger improvement.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-out", type=Path, required=True)
    parser.add_argument("--md-out", type=Path, required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    payload = build(DEFAULT_SOURCES)
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.md_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(
        json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True) + "\n"
    )
    args.md_out.write_text(render_markdown(payload) + "\n")
    print(
        json.dumps(
            {
                "status": payload["status"],
                "route_count": payload["route_count"],
                "accepted_route_count": payload["accepted_route_count"],
                "rejected_route_count": payload["rejected_route_count"],
                "recommended_next_route_count": payload["recommended_next_route_count"],
                "validation_error_count": payload["validation_error_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["validation_error_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
