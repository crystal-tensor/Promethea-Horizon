#!/usr/bin/env python3
"""T-B1-004fq/T-B7-014z: R67 accepted-exit-route submission contract gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r67_exit_route_submission_contract_gate_v0"
STATUS = "cone01_r67_exit_route_submission_contract_emitted_zero_credit"
MODEL_STATUS = "accepted_exit_route_contract_exists_but_placeholder_submission_rejected"
VERSION = "0.1"
TARGET_ID = "T-B1-004fq/T-B7-014z"
UPSTREAM_TARGET_ID = "T-B1-004fp/T-B7-014y"
CONTRACT_ID = "B1-B7-cone01-R67-accepted-exit-route-submission-contract"
TEMPLATE_ID = "B1-B7-cone01-R67-accepted-exit-route-submission-template"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def req(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_contract(r66: dict[str, Any], r5: dict[str, Any]) -> dict[str, Any]:
    r66_summary = r66["summary"]
    r5_summary = r5["summary"]
    contract = {
        "contract_id": CONTRACT_ID,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r66_retest_packet_hash": r66_summary["r66_retest_packet_hash"],
        "source_r5_exit_route_selector_hash": r5_summary.get("selector_hash"),
        "accepted_route_classes": [
            {
                "route_id": "R1-line1381-resolution",
                "route_target": "eliminate_absorb_or_honestly_price_line1381_off_grid_local_u3",
                "minimum_required_delta": {
                    "accepted_exit_route_count": 1,
                    "occurrence_removal_delta_min": 1,
                    "proxy_t_reduction_delta_min": 1,
                },
            },
            {
                "route_id": "R2-line1378-overlap-recovery",
                "route_target": "recover_or_account_for_line1378_without_double_counting",
                "minimum_required_delta": {
                    "accepted_exit_route_count": 1,
                    "occurrence_removal_delta_min": 1,
                    "proxy_t_reduction_delta_min": 1,
                },
            },
            {
                "route_id": "R3-thirty-certificate-batch",
                "route_target": "submit_30_occurrence_removing_certificates_and_600_proxy_t_delta",
                "minimum_required_delta": {
                    "accepted_exit_route_count": 1,
                    "occurrence_removal_delta_min": 30,
                    "proxy_t_reduction_delta_min": 600,
                },
            },
        ],
        "required_submission_fields": [
            "route_id",
            "route_class",
            "source_r66_retest_packet_hash",
            "full_circuit_rewrite_artifact_path",
            "full_circuit_rewrite_artifact_sha256",
            "source_openqasm3_path",
            "candidate_openqasm3_path",
            "source_openqasm3_sha256",
            "candidate_openqasm3_sha256",
            "machine_check_replay_command",
            "machine_check_replay_stdout_path",
            "machine_check_replay_stdout_sha256",
            "semantic_or_symbolic_equivalence_certificate_path",
            "semantic_or_symbolic_equivalence_certificate_sha256",
            "no_double_counting_ledger_path",
            "no_double_counting_ledger_sha256",
            "line1381_pricing_or_elimination_evidence_path",
            "line1381_pricing_or_elimination_evidence_sha256",
            "line1378_recovery_or_exclusion_evidence_path",
            "line1378_recovery_or_exclusion_evidence_sha256",
            "occurrence_delta_ledger_path",
            "occurrence_delta_ledger_sha256",
            "proxy_t_delta_ledger_path",
            "proxy_t_delta_ledger_sha256",
            "accepted_exit_route_count",
            "occurrence_removal_delta",
            "proxy_t_reduction_delta",
            "b7_nonzero_retest_requested",
            "claim_boundary",
        ],
        "acceptance_rules": [
            "all required_submission_fields are non-placeholder and hash-bound",
            "source_r66_retest_packet_hash equals the current R66 packet hash",
            "machine_check_replay_command can reproduce the submitted full-circuit rewrite artifact",
            "semantic_or_symbolic_equivalence_certificate covers the full circuit or explicitly bounded route class",
            "no_double_counting_ledger accounts for selected lines [268, 1381] and dropped overlap line [1378]",
            "occurrence_removal_delta and proxy_t_reduction_delta are positive",
            "claim_boundary forbids O3 closure, reroute, and B7 credit until a downstream nonzero ledger retest accepts the submitted deltas",
        ],
        "forbidden_shortcuts": [
            "row-level R63/R64/R65/R66 denominator evidence alone",
            "unhashed markdown-only claims",
            "single-row local rewrite without full-circuit or route-bounded replay",
            "nonzero B7 credit without accepted occurrence/proxy-T delta",
            "double-counting line1378 and line1381 deltas",
        ],
    }
    contract["contract_hash"] = stable_hash(contract)
    return contract


def build_template(contract: dict[str, Any]) -> dict[str, Any]:
    template = {
        "template_id": TEMPLATE_ID,
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "route_id": None,
        "route_class": None,
        "source_r66_retest_packet_hash": contract["source_r66_retest_packet_hash"],
        "full_circuit_rewrite_artifact_path": None,
        "full_circuit_rewrite_artifact_sha256": None,
        "source_openqasm3_path": None,
        "candidate_openqasm3_path": None,
        "source_openqasm3_sha256": None,
        "candidate_openqasm3_sha256": None,
        "machine_check_replay_command": None,
        "machine_check_replay_stdout_path": None,
        "machine_check_replay_stdout_sha256": None,
        "semantic_or_symbolic_equivalence_certificate_path": None,
        "semantic_or_symbolic_equivalence_certificate_sha256": None,
        "no_double_counting_ledger_path": None,
        "no_double_counting_ledger_sha256": None,
        "line1381_pricing_or_elimination_evidence_path": None,
        "line1381_pricing_or_elimination_evidence_sha256": None,
        "line1378_recovery_or_exclusion_evidence_path": None,
        "line1378_recovery_or_exclusion_evidence_sha256": None,
        "occurrence_delta_ledger_path": None,
        "occurrence_delta_ledger_sha256": None,
        "proxy_t_delta_ledger_path": None,
        "proxy_t_delta_ledger_sha256": None,
        "accepted_exit_route_count": 0,
        "occurrence_removal_delta": 0,
        "proxy_t_reduction_delta": 0,
        "b7_nonzero_retest_requested": False,
        "claim_boundary": (
            "Template only. No O3 closure, reroute permission, resource saving, "
            "or B7 ledger credit is claimed until a nonzero ledger retest accepts "
            "a complete exit-route submission."
        ),
    }
    template["template_hash"] = stable_hash(template)
    return template


def preflight_template(contract: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    placeholder_fields = [
        field for field in contract["required_submission_fields"] if template.get(field) in (None, "")
    ]
    zero_delta_fields = [
        field
        for field in [
            "accepted_exit_route_count",
            "occurrence_removal_delta",
            "proxy_t_reduction_delta",
        ]
        if template.get(field) == 0
    ]
    verdict = {
        "artifact": "R67 accepted-exit-route template preflight",
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "template_id": template["template_id"],
        "template_hash": template["template_hash"],
        "placeholder_field_count": len(placeholder_fields),
        "placeholder_fields": placeholder_fields,
        "zero_delta_fields": zero_delta_fields,
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_credit_delta": 0,
        "b7_nonzero_retest_allowed": False,
        "preflight_passed": False,
        "rejection_reason": "template_has_placeholders_and_zero_deltas",
    }
    verdict["preflight_hash"] = stable_hash(verdict)
    return verdict


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r66 = load_json(args.r66_result)
    r5 = load_json(args.r5_selector)
    contract = build_contract(r66, r5)
    template = build_template(contract)
    preflight = preflight_template(contract, template)
    write_json(args.contract_output, contract)
    write_json(args.template_output, template)
    write_json(args.preflight_output, preflight)
    requirements = [
        req(
            "E1",
            "R66 upstream completed the zero-credit B7 retest boundary",
            r66["summary"]["ledger_retest_boundary_complete"] is True
            and r66["summary"]["ledger_credit_admissible_row_count"] == 0
            and r66["summary"]["b7_credit_delta"] == 0,
            {
                "source_r66_retest_packet_hash": r66["summary"]["r66_retest_packet_hash"],
                "ledger_credit_admissible_row_count": r66["summary"][
                    "ledger_credit_admissible_row_count"
                ],
                "b7_credit_delta": r66["summary"]["b7_credit_delta"],
            },
        ),
        req(
            "E2",
            "R67 contract defines R1/R2/R3 exit-route classes",
            len(contract["accepted_route_classes"]) == 3
            and [row["route_id"] for row in contract["accepted_route_classes"]]
            == [
                "R1-line1381-resolution",
                "R2-line1378-overlap-recovery",
                "R3-thirty-certificate-batch",
            ],
            {"accepted_route_classes": contract["accepted_route_classes"]},
        ),
        req(
            "E3",
            "R67 contract requires full-circuit or route-bounded replay evidence",
            "full_circuit_rewrite_artifact_path" in contract["required_submission_fields"]
            and "machine_check_replay_command" in contract["required_submission_fields"]
            and "semantic_or_symbolic_equivalence_certificate_path"
            in contract["required_submission_fields"],
            {"required_submission_fields": contract["required_submission_fields"]},
        ),
        req(
            "E4",
            "R67 contract requires no-double-counting, line1381, line1378, and delta ledgers",
            all(
                field in contract["required_submission_fields"]
                for field in [
                    "no_double_counting_ledger_path",
                    "line1381_pricing_or_elimination_evidence_path",
                    "line1378_recovery_or_exclusion_evidence_path",
                    "occurrence_delta_ledger_path",
                    "proxy_t_delta_ledger_path",
                ]
            ),
            {"required_submission_fields": contract["required_submission_fields"]},
        ),
        req(
            "E5",
            "R67 template is emitted but rejected as a placeholder",
            preflight["preflight_passed"] is False
            and preflight["placeholder_field_count"] > 0
            and preflight["accepted_exit_route_count"] == 0,
            {
                "placeholder_field_count": preflight["placeholder_field_count"],
                "accepted_exit_route_count": preflight["accepted_exit_route_count"],
            },
        ),
        req(
            "E6",
            "R67 preserves zero B7 credit and blocks nonzero retest",
            preflight["b7_credit_delta"] == 0
            and preflight["b7_nonzero_retest_allowed"] is False
            and template["b7_nonzero_retest_requested"] is False,
            {
                "b7_credit_delta": preflight["b7_credit_delta"],
                "b7_nonzero_retest_allowed": preflight["b7_nonzero_retest_allowed"],
                "b7_nonzero_retest_requested": template["b7_nonzero_retest_requested"],
            },
        ),
        req(
            "E7",
            "R67 forbids row-level denominator evidence from counting alone",
            "row-level R63/R64/R65/R66 denominator evidence alone"
            in contract["forbidden_shortcuts"],
            {"forbidden_shortcuts": contract["forbidden_shortcuts"]},
        ),
        req(
            "E8",
            "R67 artifacts are hash-bound and written",
            all(
                path.is_file()
                for path in [
                    args.contract_output,
                    args.template_output,
                    args.preflight_output,
                ]
            )
            and bool(contract["contract_hash"])
            and bool(template["template_hash"])
            and bool(preflight["preflight_hash"]),
            {
                "contract_hash": contract["contract_hash"],
                "template_hash": template["template_hash"],
                "preflight_hash": preflight["preflight_hash"],
            },
        ),
    ]
    failed = [item["requirement_id"] for item in requirements if not item["passed"]]
    summary = {
        "source_r66_retest_packet_hash": r66["summary"]["r66_retest_packet_hash"],
        "contract_id": contract["contract_id"],
        "contract_hash": contract["contract_hash"],
        "contract_file_sha256": file_hash(args.contract_output),
        "template_id": template["template_id"],
        "template_hash": template["template_hash"],
        "template_file_sha256": file_hash(args.template_output),
        "preflight_hash": preflight["preflight_hash"],
        "preflight_file_sha256": file_hash(args.preflight_output),
        "route_class_count": len(contract["accepted_route_classes"]),
        "required_submission_field_count": len(contract["required_submission_fields"]),
        "placeholder_field_count": preflight["placeholder_field_count"],
        "preflight_passed": preflight["preflight_passed"],
        "accepted_exit_route_count": 0,
        "accepted_occurrence_removal": 0,
        "accepted_proxy_t_reduction": 0,
        "b7_nonzero_retest_allowed": False,
        "b7_credit_delta": 0,
        "resource_saving_claimed": False,
        "b7_ledger_improvement_claimed": False,
        "o3_closed": False,
        "reroute_allowed": False,
        "remaining_open_obligations": [
            "filled_exit_route_submission",
            "machine_checked_full_circuit_or_route_bounded_replay",
            "nonzero_occurrence_and_proxy_t_delta",
            "downstream_nonzero_b7_ledger_retest",
        ],
        "remaining_open_obligation_count": 4,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed),
        "requirements_failed": len(failed),
        "failed_requirement_ids": failed,
        "validation_error_count": len(failed),
    }
    return {
        "title": "B1/B7 Cone01 R67 Accepted-Exit-Route Submission Contract Gate",
        "version": VERSION,
        "last_updated": "2026-07-09",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "r67_exit_route_submission_contract_packet": {
            "source_r66_result": str(args.r66_result),
            "source_r5_selector": str(args.r5_selector),
            "contract_output": str(args.contract_output),
            "template_output": str(args.template_output),
            "preflight_output": str(args.preflight_output),
            "contract": contract,
            "template": template,
            "preflight": preflight,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R67 emits a hash-bound accepted-exit-route submission contract, "
                "template, and placeholder preflight rejection for the post-R66 path."
            ),
            "what_is_not_supported": (
                "R67 does not accept an exit route, prove a full-circuit rewrite, "
                "allow reroute, or grant any B7 ledger credit."
            ),
            "next_gate": (
                "Fill the R67 template with source-backed replay, no-double-counting, "
                "line1381/line1378, occurrence-delta, and proxy-T-delta evidence."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    s = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R67 Accepted-Exit-Route Submission Contract Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Contract hash: `{s['contract_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R67 passes {s['requirements_passed']}/{s['requirement_count']} "
            "requirements by emitting the accepted-exit-route contract and rejecting "
            "the placeholder template. It creates a PR target, not an accepted route."
        ),
        "",
        "## Evidence",
        "",
        f"- Route classes: `{s['route_class_count']}`",
        f"- Required submission fields: `{s['required_submission_field_count']}`",
        f"- Placeholder fields rejected: `{s['placeholder_field_count']}`",
        f"- Preflight passed: `{s['preflight_passed']}`",
        f"- Accepted exit routes: `{s['accepted_exit_route_count']}`",
        f"- Accepted occurrence removal: `{s['accepted_occurrence_removal']}`",
        f"- Accepted proxy-T reduction: `{s['accepted_proxy_t_reduction']}`",
        f"- B7 nonzero retest allowed: `{s['b7_nonzero_retest_allowed']}`",
        f"- B7 credit delta: `{s['b7_credit_delta']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        lines.append(f"- `{item['requirement_id']}` {'PASS' if item['passed'] else 'FAIL'}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            "## Remaining Open Obligations",
            "",
        ]
    )
    for item in s["remaining_open_obligations"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"- validation_error_count: `{s['validation_error_count']}`", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r66-result",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R66_o3_f4_b7_zero_credit_ledger_retest_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--r5-selector",
        type=Path,
        default=Path("results/B1_B7_cone01_R5_exit_route_priority_selector_v0.json"),
    )
    parser.add_argument(
        "--contract-output",
        type=Path,
        default=Path(f"{SUBMISSION_DIR}/R67-accepted-exit-route.contract.json"),
    )
    parser.add_argument(
        "--template-output",
        type=Path,
        default=Path(f"{SUBMISSION_DIR}/R67-accepted-exit-route.template.json"),
    )
    parser.add_argument(
        "--preflight-output",
        type=Path,
        default=Path(f"{SUBMISSION_DIR}/R67-accepted-exit-route.template_preflight.json"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_R67_exit_route_submission_contract_gate_v0.json"
        ),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path(
            "research/B1_B7_cone01_R67_exit_route_submission_contract_gate.md"
        ),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        s = payload["summary"]
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": s["requirements_passed"],
                    "requirements_failed": s["requirements_failed"],
                    "route_class_count": s["route_class_count"],
                    "required_submission_field_count": s[
                        "required_submission_field_count"
                    ],
                    "placeholder_field_count": s["placeholder_field_count"],
                    "accepted_exit_route_count": s["accepted_exit_route_count"],
                    "b7_credit_delta": s["b7_credit_delta"],
                    "contract_hash": s["contract_hash"],
                    "json_output": str(args.json_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
