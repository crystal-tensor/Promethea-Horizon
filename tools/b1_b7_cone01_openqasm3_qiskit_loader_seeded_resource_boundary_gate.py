#!/usr/bin/env python3
"""Resource-boundary gate for Qiskit-loader seeded product replay evidence.

T-B1-004co strengthens semantic replay pressure on the OpenQASM 3 candidate,
but semantic replay is not the same as a B7 resource win. This gate explicitly
joins that replay evidence to the current line-1381 local-U3 pricing boundary
and the rejected shared-theta B7 ledger refresh.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESEARCH = ROOT / "research"

METHOD = "b1_b7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate_v0"
STATUS = "cone01_openqasm3_qiskit_loader_seeded_resource_boundary_no_b7_credit"
MODEL_STATUS = "seeded_replay_evidence_does_not_clear_line1381_or_b7_ledger_boundary"

SEEDED_REPLAY_PATH = (
    RESULTS / "B1_B7_cone01_openqasm3_qiskit_loader_seeded_product_replay_gate_v0.json"
)
LINE1381_PRICING_PATH = RESULTS / "B1_B7_cone01_line1381_local_u3_pricing_gate_v0.json"
THETA_COST_MODEL_PATH = RESULTS / "B1_B7_cone01_theta_sharing_cost_model_gate_v0.json"
REFRESHED_B7_LEDGER_PATH = (
    RESULTS / "B1_B7_cone01_shared_theta_refreshed_b7_ledger_gate_v0.json"
)
OUT_JSON = (
    RESULTS
    / "B1_B7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate_v0.json"
)
OUT_MD = RESEARCH / "B1_B7_cone01_openqasm3_qiskit_loader_seeded_resource_boundary_gate.md"


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    seeded_payload = load_json(SEEDED_REPLAY_PATH)
    pricing_payload = load_json(LINE1381_PRICING_PATH)
    cost_payload = load_json(THETA_COST_MODEL_PATH)
    refresh_payload = load_json(REFRESHED_B7_LEDGER_PATH)

    seeded_summary = seeded_payload["summary"]
    pricing_summary = pricing_payload["summary"]
    cost_summary = cost_payload["summary"]
    refresh_summary = refresh_payload["summary"]

    blockers = [
        {
            "blocker_id": "RB-01",
            "name": "line1381_off_grid_local_u3_pressure",
            "current_value": pricing_summary["line1381_replacement_off_pi_over_four_parameter_count"],
            "required_value": 0,
            "passed": False,
            "reason": "Line 1381 still has five off-grid local-U3 parameters.",
        },
        {
            "blocker_id": "RB-02",
            "name": "line1378_overlap_delta_not_recovered",
            "current_value": pricing_summary["line1378_delta_recovered"],
            "required_value": True,
            "passed": False,
            "reason": "The dropped overlap line 1378 delta remains unrecovered.",
        },
        {
            "blocker_id": "RB-03",
            "name": "accepted_occurrence_removal",
            "current_value": pricing_summary["accepted_occurrence_removal"],
            "required_value": 30,
            "passed": False,
            "reason": "No occurrence-removing certificate is accepted by the B7 ledger.",
        },
        {
            "blocker_id": "RB-04",
            "name": "theta_cost_model_accepted",
            "current_value": cost_summary["cost_model_accepted"],
            "required_value": True,
            "passed": False,
            "reason": "The shared-theta physical cost model is still rejected.",
        },
        {
            "blocker_id": "RB-05",
            "name": "refreshed_b7_ledger_accepts_theta_sharing",
            "current_value": refresh_summary["b7_ledger_accepts_theta_sharing"],
            "required_value": True,
            "passed": False,
            "reason": "The explicit B7 ledger refresh rejects theta sharing as counted savings.",
        },
    ]
    failed_blockers = [row for row in blockers if not row["passed"]]
    seeded_replay_passed = bool(seeded_summary["qiskit_loader_seeded_product_replay_passed"])
    resource_boundary_passed = seeded_replay_passed and len(failed_blockers) == len(blockers)
    errors: list[str] = []
    expected = {
        "seeded_status": "cone01_openqasm3_qiskit_loader_seeded_product_replay_passed_without_b7_credit",
        "pricing_status": "cone01_line1381_local_u3_pricing_boundary_no_b7_credit",
        "cost_status": "cone01_theta_sharing_cost_model_not_accepted",
        "refresh_status": "cone01_shared_theta_refreshed_b7_ledger_rejected",
        "seeded_cases": 16,
        "line1381_off_grid": 5,
        "line1381_proxy_t_pressure": 100,
        "cost_pass_count": 6,
        "cost_fail_count": 2,
        "missing_proxy_t": 600,
    }
    observed = {
        "seeded_status": seeded_payload["status"],
        "pricing_status": pricing_payload["status"],
        "cost_status": cost_payload["status"],
        "refresh_status": refresh_payload["status"],
        "seeded_cases": seeded_summary["input_case_count"],
        "line1381_off_grid": pricing_summary["line1381_replacement_off_pi_over_four_parameter_count"],
        "line1381_proxy_t_pressure": pricing_summary["line1381_unpriced_proxy_t_pressure"],
        "cost_pass_count": cost_summary["cost_model_acceptance_pass_count"],
        "cost_fail_count": cost_summary["cost_model_acceptance_fail_count"],
        "missing_proxy_t": refresh_summary["missing_proxy_t_ledger_reduction_for_gcm_h6_1_20"],
    }
    for key, value in expected.items():
        if observed[key] != value:
            errors.append(f"{key} expected {value}, got {observed[key]}")
    if not seeded_replay_passed:
        errors.append("seeded replay should pass before evaluating this resource boundary")
    if any(row["passed"] for row in blockers):
        errors.append("current boundary expects every resource blocker to remain failed")

    summary = {
        "source_qiskit_loader_seeded_product_replay_gate": rel(SEEDED_REPLAY_PATH),
        "source_line1381_local_u3_pricing_gate": rel(LINE1381_PRICING_PATH),
        "source_theta_sharing_cost_model_gate": rel(THETA_COST_MODEL_PATH),
        "source_shared_theta_refreshed_b7_ledger_gate": rel(REFRESHED_B7_LEDGER_PATH),
        "qiskit_loader_seeded_product_replay_passed": seeded_replay_passed,
        "seeded_product_input_case_count": seeded_summary["input_case_count"],
        "seeded_product_min_state_fidelity": seeded_summary["min_state_fidelity"],
        "seeded_product_max_probability_delta": seeded_summary["max_probability_delta"],
        "line1381_replacement_off_pi_over_four_parameter_count": pricing_summary[
            "line1381_replacement_off_pi_over_four_parameter_count"
        ],
        "line1381_unpriced_proxy_t_pressure": pricing_summary[
            "line1381_unpriced_proxy_t_pressure"
        ],
        "line1378_delta_recovered": pricing_summary["line1378_delta_recovered"],
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "theta_cost_model_accepted": cost_summary["cost_model_accepted"],
        "theta_cost_model_acceptance_pass_count": cost_summary["cost_model_acceptance_pass_count"],
        "theta_cost_model_acceptance_fail_count": cost_summary["cost_model_acceptance_fail_count"],
        "refreshed_b7_ledger_accepts_theta_sharing": refresh_summary[
            "b7_ledger_accepts_theta_sharing"
        ],
        "missing_proxy_t_ledger_reduction_for_gcm_h6_1_20": refresh_summary[
            "missing_proxy_t_ledger_reduction_for_gcm_h6_1_20"
        ],
        "resource_boundary_blocker_count": len(blockers),
        "resource_boundary_failed_blocker_count": len(failed_blockers),
        "resource_boundary_blockers": blockers,
        "resource_boundary_passed": resource_boundary_passed,
        "accepted_qiskit_loader_seeded_resource_boundary_count": (
            1 if resource_boundary_passed and not errors else 0
        ),
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "validation_error_count": len(errors),
    }
    payload = {
        "benchmark_id": "B1",
        "linked_b7_problem_id": 21,
        "method": METHOD,
        "status": STATUS if not errors else "cone01_openqasm3_qiskit_loader_seeded_resource_boundary_failed",
        "model_status": MODEL_STATUS if not errors else "seeded_resource_boundary_validation_failed",
        "workload": "qasmbench_medium_exact/gcm_h6.qasm",
        "claim_boundary": {
            "supported_claim": (
                "The Qiskit-loader seeded product-state replay evidence is accepted as "
                "semantic pressure, but it does not clear line-1381 local-U3 pricing, "
                "line-1378 overlap recovery, occurrence removal, or the B7 ledger refresh."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
            "unsupported_claims": [
                "This does not claim arbitrary-input or symbolic equivalence.",
                "This does not price, eliminate, or absorb the line-1381 local-U3 parameters.",
                "This does not recover the dropped line-1378 overlap delta.",
                "This does not accept shared-theta reuse as a physical B7 saving.",
                "This does not reduce the B7 proxy-T ledger.",
            ],
            "next_gate": (
                "A useful follow-up must remove or price the line-1381 burden, recover "
                "line 1378 without double-counting, or produce accepted occurrence-removing "
                "certificates that change the refreshed B7 ledger."
            ),
        },
        "summary": summary,
        "validation_errors": errors,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if errors:
        raise SystemExit("seeded resource boundary validation failed: " + "; ".join(errors))


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    claims = payload["claim_boundary"]
    lines = [
        "# B1/B7 cone_01 OpenQASM 3 Qiskit-Loader Seeded Resource Boundary Gate",
        "",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Workload: `{payload['workload']}`",
        f"- Supported claim: {claims['supported_claim']}",
        "",
        "## Inputs",
        "",
        f"- Seeded product replay gate: `{summary['source_qiskit_loader_seeded_product_replay_gate']}`",
        f"- Line-1381 pricing gate: `{summary['source_line1381_local_u3_pricing_gate']}`",
        f"- Theta-sharing cost model gate: `{summary['source_theta_sharing_cost_model_gate']}`",
        f"- Refreshed B7 ledger gate: `{summary['source_shared_theta_refreshed_b7_ledger_gate']}`",
        "",
        "## Decision",
        "",
        f"- Seeded replay passed / cases: `{summary['qiskit_loader_seeded_product_replay_passed']}` / `{summary['seeded_product_input_case_count']}`",
        f"- Seeded replay min fidelity / max probability delta: `{summary['seeded_product_min_state_fidelity']}` / `{summary['seeded_product_max_probability_delta']}`",
        f"- Line-1381 off-grid local-U3 parameters / proxy-T pressure: `{summary['line1381_replacement_off_pi_over_four_parameter_count']}` / `{summary['line1381_unpriced_proxy_t_pressure']}`",
        f"- Line-1378 delta recovered: `{summary['line1378_delta_recovered']}`",
        f"- Theta cost model accepted / pass / fail: `{summary['theta_cost_model_accepted']}` / `{summary['theta_cost_model_acceptance_pass_count']}` / `{summary['theta_cost_model_acceptance_fail_count']}`",
        f"- Refreshed B7 ledger accepts theta sharing: `{summary['refreshed_b7_ledger_accepts_theta_sharing']}`",
        f"- Missing proxy-T ledger reduction for gcm_h6 1.20x: `{summary['missing_proxy_t_ledger_reduction_for_gcm_h6_1_20']}`",
        f"- Accepted occurrence / proxy-T reduction: `{summary['accepted_occurrence_removal']}` / `{summary['accepted_proxy_t_reduction']}`",
        f"- Accepted seeded resource-boundary artifact: `{summary['accepted_qiskit_loader_seeded_resource_boundary_count']}`",
        "",
        "## Resource Blockers",
        "",
    ]
    for row in summary["resource_boundary_blockers"]:
        lines.append(
            f"- `{row['blocker_id']}` {row['name']}: current `{row['current_value']}`, "
            f"required `{row['required_value']}`; passed `{row['passed']}`. {row['reason']}"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            *[f"- {claim}" for claim in claims["unsupported_claims"]],
            "",
            "## Validation",
            "",
            f"- Resource boundary passed: `{summary['resource_boundary_passed']}`",
            f"- Validation errors: `{summary['validation_error_count']}`",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
