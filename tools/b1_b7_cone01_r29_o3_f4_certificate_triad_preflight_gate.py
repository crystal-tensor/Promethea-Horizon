#!/usr/bin/env python3
"""T-B1-004ee/T-B7-013n: R29 O3-F4 certificate-triad preflight gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r29_o3_f4_certificate_triad_preflight_gate_v0"
STATUS = "cone01_r29_o3_f4_template_submission_rejected_by_preflight"
MODEL_STATUS = "o3_f4_template_placeholder_rejected_no_o3_no_reroute"
VERSION = "0.1"
TARGET_ID = "T-B1-004ee/T-B7-013n"
UPSTREAM_TARGET_ID = "T-B1-004ed/T-B7-013m"
R28_TARGET_ID = "T-B1-004ed/T-B7-013m"
FAMILY_ID = "O3-F4"
CANDIDATE_ID = "NL-C02"
STRICT_TOLERANCE = 1.0e-8
REQUIRED_GATES = [
    "C1-source-lineage",
    "C2-strict-replay-under-tolerance",
    "C3-replay-certificate-complete",
    "C4-denominator-comparison-complete",
    "C5-same-access-model",
    "C6-leakage-free-optimizer-trace",
    "C7-machine-check-replay",
    "C8-claim-boundary-zero-credit-until-accepted",
    "C9-hash-bound-evidence-bundle",
]
TEMPLATE_MARKERS = ("<", ">", "required")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2 if pretty else None, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def requirement(
    requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]
) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def contains_template_marker(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in TEMPLATE_MARKERS)
    if isinstance(value, list):
        return any(contains_template_marker(item) for item in value)
    if isinstance(value, dict):
        return any(contains_template_marker(item) for item in value.values())
    return False


def gate_result(gate_id: str, passed: bool, reason: str, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "gate_id": gate_id,
        "passed": bool(passed),
        "reason": reason,
        "evidence": evidence,
    }


def evaluate_template_as_submission(r28: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    contract = r28["o3_f4_certificate_triad_contract_packet"]["contract"]
    required_fields = contract["required_fields"]
    missing_fields = [field for field in required_fields if field not in template]
    placeholder_fields = [
        field for field in required_fields if field in template and contains_template_marker(template[field])
    ]
    replay_rows = template.get("unitary_replay_protocol", {}).get("replay_rows", [])
    comparison_table = template.get("same_access_denominator_comparison", {}).get("comparison_table", [])
    challenge_rows_covered = template.get("challenge_rows_covered")
    r11_r12_rows_covered = template.get("r11_r12_rows_covered")
    checker_returncode = template.get("checker_returncode")
    same_access = template.get("same_access_denominator_comparison", {}).get("same_access_model")
    leakage_packet_visible = template.get("leakage_free_optimizer_trace", {}).get(
        "challenge_packet_visible_to_optimizer"
    )
    hidden_restart_count = template.get("leakage_free_optimizer_trace", {}).get(
        "hidden_restart_count"
    )

    gates = [
        gate_result(
            "C1-source-lineage",
            template.get("source_target_id") == R28_TARGET_ID
            and template.get("family_id") == FAMILY_ID
            and template.get("candidate_id") == CANDIDATE_ID
            and not missing_fields,
            "source lineage and required field surface are present",
            {
                "source_target_id": template.get("source_target_id"),
                "missing_fields": missing_fields,
            },
        ),
        gate_result(
            "C2-strict-replay-under-tolerance",
            isinstance(replay_rows, list)
            and len(replay_rows) == 8
            and not contains_template_marker(template.get("unitary_replay_protocol"))
            and template.get("unitary_replay_protocol", {}).get("tolerance") == STRICT_TOLERANCE,
            "template has no measured replay rows under strict tolerance",
            {
                "replay_row_count": len(replay_rows) if isinstance(replay_rows, list) else None,
                "required_replay_row_count": 8,
                "strict_tolerance": STRICT_TOLERANCE,
            },
        ),
        gate_result(
            "C3-replay-certificate-complete",
            not contains_template_marker(template.get("same_unitary_replay_certificate")),
            "template contains replay-certificate placeholders",
            {
                "certificate_type": template.get("same_unitary_replay_certificate", {}).get(
                    "certificate_type"
                ),
                "certificate_hash": template.get("same_unitary_replay_certificate", {}).get(
                    "certificate_hash"
                ),
            },
        ),
        gate_result(
            "C4-denominator-comparison-complete",
            isinstance(comparison_table, list)
            and len(comparison_table) >= contract.get("minimum_denominator_rows", 31)
            and r11_r12_rows_covered == contract.get("minimum_denominator_rows", 31),
            "template has no complete denominator comparison table",
            {
                "comparison_row_count": len(comparison_table)
                if isinstance(comparison_table, list)
                else None,
                "r11_r12_rows_covered": r11_r12_rows_covered,
                "required_r11_r12_rows": contract.get("minimum_denominator_rows", 31),
            },
        ),
        gate_result(
            "C5-same-access-model",
            same_access is True
            and not contains_template_marker(
                template.get("same_access_denominator_comparison", {}).get("denominator_hash")
            ),
            "same-access flag is true but the denominator evidence remains a placeholder",
            {
                "same_access_model": same_access,
                "denominator_hash": template.get("same_access_denominator_comparison", {}).get(
                    "denominator_hash"
                ),
            },
        ),
        gate_result(
            "C6-leakage-free-optimizer-trace",
            leakage_packet_visible is False
            and hidden_restart_count == 0
            and not contains_template_marker(template.get("leakage_free_optimizer_trace")),
            "optimizer trace hashes remain placeholders",
            {
                "challenge_packet_visible_to_optimizer": leakage_packet_visible,
                "hidden_restart_count": hidden_restart_count,
                "seed_schedule_hash": template.get("leakage_free_optimizer_trace", {}).get(
                    "seed_schedule_hash"
                ),
                "optimizer_trace_hash": template.get("leakage_free_optimizer_trace", {}).get(
                    "optimizer_trace_hash"
                ),
            },
        ),
        gate_result(
            "C7-machine-check-replay",
            checker_returncode == 0
            and not contains_template_marker(template.get("checker_stdout_hash"))
            and not contains_template_marker(template.get("offline_bundle_hash"))
            and not contains_template_marker(template.get("artifact_hash")),
            "machine-check and offline-bundle hashes remain placeholders",
            {
                "checker_returncode": checker_returncode,
                "checker_stdout_hash": template.get("checker_stdout_hash"),
                "offline_bundle_hash": template.get("offline_bundle_hash"),
                "artifact_hash": template.get("artifact_hash"),
            },
        ),
        gate_result(
            "C8-claim-boundary-zero-credit-until-accepted",
            template.get("o3_closed") is False
            and template.get("reroute_allowed") is False
            and template.get("b7_credit_delta") == 0,
            "claim boundary keeps zero credit before acceptance",
            {
                "o3_closed": template.get("o3_closed"),
                "reroute_allowed": template.get("reroute_allowed"),
                "b7_credit_delta": template.get("b7_credit_delta"),
            },
        ),
        gate_result(
            "C9-hash-bound-evidence-bundle",
            bool(template.get("template_hash")) and not missing_fields,
            "template is hash-bound but not evidence-complete",
            {
                "template_hash": template.get("template_hash"),
                "missing_fields": missing_fields,
            },
        ),
    ]
    passed_gate_ids = [item["gate_id"] for item in gates if item["passed"]]
    failed_gate_ids = [item["gate_id"] for item in gates if not item["passed"]]
    result = {
        "submission_kind": "r28_template_used_as_placeholder_submission",
        "accepted": False,
        "passed_gate_ids": passed_gate_ids,
        "failed_gate_ids": failed_gate_ids,
        "placeholder_field_count": len(placeholder_fields),
        "placeholder_fields": placeholder_fields,
        "missing_required_fields": missing_fields,
        "challenge_rows_covered": challenge_rows_covered,
        "r11_r12_rows_covered": r11_r12_rows_covered,
        "gate_results": gates,
    }
    result["preflight_hash"] = stable_hash(result)
    return result


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    r28 = load_json(args.r28_contract)
    template = load_json(args.template_submission)
    preflight = evaluate_template_as_submission(r28, template)
    expected_failed = [
        "C2-strict-replay-under-tolerance",
        "C3-replay-certificate-complete",
        "C4-denominator-comparison-complete",
        "C5-same-access-model",
        "C6-leakage-free-optimizer-trace",
        "C7-machine-check-replay",
    ]
    template_sha256 = file_hash(args.template_submission)
    r28_summary = r28["summary"]
    requirements = [
        requirement(
            "S1",
            "R28 contract source is validation-clean and binds the O3-F4 template",
            r28_summary.get("validation_error_count") == 0
            and r28_summary.get("template_hash") == template.get("template_hash"),
            {
                "r28_validation_error_count": r28_summary.get("validation_error_count"),
                "r28_template_hash": r28_summary.get("template_hash"),
                "template_hash": template.get("template_hash"),
            },
        ),
        requirement(
            "S2",
            "Template-as-submission has every required field but still contains placeholders",
            not preflight["missing_required_fields"]
            and preflight["placeholder_field_count"] >= 10,
            {
                "missing_required_fields": preflight["missing_required_fields"],
                "placeholder_field_count": preflight["placeholder_field_count"],
                "placeholder_fields": preflight["placeholder_fields"],
            },
        ),
        requirement(
            "S3",
            "Preflight rejects the template and does not accept an O3-F4 artifact",
            preflight["accepted"] is False,
            {"accepted": preflight["accepted"], "failed_gate_ids": preflight["failed_gate_ids"]},
        ),
        requirement(
            "S4",
            "The failed gates are the evidence-heavy gates C2 through C7",
            preflight["failed_gate_ids"] == expected_failed,
            {
                "expected_failed_gate_ids": expected_failed,
                "actual_failed_gate_ids": preflight["failed_gate_ids"],
            },
        ),
        requirement(
            "S5",
            "Surface lineage, zero-credit claim boundary, and template hash gates still pass",
            preflight["passed_gate_ids"]
            == [
                "C1-source-lineage",
                "C8-claim-boundary-zero-credit-until-accepted",
                "C9-hash-bound-evidence-bundle",
            ],
            {"passed_gate_ids": preflight["passed_gate_ids"]},
        ),
        requirement(
            "S6",
            "Strict replay and denominator obligations remain unfilled",
            template.get("challenge_rows_covered") != 8
            and template.get("r11_r12_rows_covered") != 31,
            {
                "challenge_rows_covered": template.get("challenge_rows_covered"),
                "required_challenge_rows": 8,
                "r11_r12_rows_covered": template.get("r11_r12_rows_covered"),
                "required_r11_r12_rows": 31,
            },
        ),
        requirement(
            "S7",
            "R29 preserves zero O3, reroute, and B7 credit claims",
            template.get("o3_closed") is False
            and template.get("reroute_allowed") is False
            and template.get("b7_credit_delta") == 0,
            {
                "o3_closed": template.get("o3_closed"),
                "reroute_allowed": template.get("reroute_allowed"),
                "b7_credit_delta": template.get("b7_credit_delta"),
            },
        ),
        requirement(
            "S8",
            "Preflight result and source template are hash-bound",
            bool(preflight["preflight_hash"]) and bool(template_sha256),
            {
                "preflight_hash": preflight["preflight_hash"],
                "template_file_sha256": template_sha256,
            },
        ),
    ]
    failed_requirements = [
        item["requirement_id"] for item in requirements if not item["passed"]
    ]
    summary = {
        "candidate_id": CANDIDATE_ID,
        "family_id": FAMILY_ID,
        "source_r28_contract_hash": r28_summary["contract_hash"],
        "source_r28_template_hash": r28_summary["template_hash"],
        "source_template_file_sha256": template_sha256,
        "preflight_hash": preflight["preflight_hash"],
        "submission_kind": preflight["submission_kind"],
        "accepted": False,
        "o3_f4_artifact_accepted": False,
        "passed_gate_count": len(preflight["passed_gate_ids"]),
        "failed_gate_count": len(preflight["failed_gate_ids"]),
        "passed_gate_ids": preflight["passed_gate_ids"],
        "failed_gate_ids": preflight["failed_gate_ids"],
        "placeholder_field_count": preflight["placeholder_field_count"],
        "strict_tolerance": STRICT_TOLERANCE,
        "challenge_rows_covered": template.get("challenge_rows_covered"),
        "required_challenge_rows": 8,
        "r11_r12_rows_covered": template.get("r11_r12_rows_covered"),
        "required_r11_r12_rows": 31,
        "same_unitary_replay_certificate_complete": False,
        "same_access_denominator_comparison_complete": False,
        "leakage_free_optimizer_trace_complete": False,
        "o3_closed": False,
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
        "remaining_open_obligations": [
            "O3-F3_symbolic_lu_artifact",
            "O3-F4_valid_certificate_triad_artifact",
            "O3-F5_route_a_artifact",
        ],
        "remaining_open_obligation_count": 3,
        "requirement_count": len(requirements),
        "requirements_passed": len(requirements) - len(failed_requirements),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "validation_error_count": len(failed_requirements),
    }
    return {
        "title": "B1/B7 Cone01 R29 O3-F4 Certificate-Triad Preflight Gate",
        "version": VERSION,
        "last_updated": "2026-07-08",
        "benchmark_id": "B1",
        "linked_benchmark_id": "B7",
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r28_target_id": R28_TARGET_ID,
        "o3_f4_certificate_triad_preflight_packet": {
            "source_r28_contract": str(args.r28_contract),
            "template_submission": str(args.template_submission),
            "template_file_sha256": template_sha256,
            "preflight_result": preflight,
        },
        "requirements": requirements,
        "summary": summary,
        "claim_boundary": {
            "what_is_supported": (
                "R29 proves the R28 template is only a placeholder: when used "
                "as a submission it is rejected on C2-C7 while the source, "
                "zero-credit, and hash-surface gates remain visible."
            ),
            "what_is_not_supported": (
                "R29 does not accept any O3-F4 artifact, does not close O3, "
                "does not permit R5 reroute, and does not create B7 credit, "
                "STV credit, or resource-saving evidence."
            ),
            "next_gate": (
                "Replace the placeholder fields with a source-backed "
                "certificate triad: strict replay rows, replay certificate, "
                "same-access denominator table, leakage-free optimizer trace, "
                "machine-check output, and hash-bound offline bundle."
            ),
            "resource_saving_claimed": False,
            "b7_ledger_improvement_claimed": False,
        },
        "validation_errors": failed_requirements,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R29 O3-F4 Certificate-Triad Preflight Gate",
        "",
        f"- Target: `{payload['source_target_id']}`",
        f"- Upstream target: `{payload['upstream_target_id']}`",
        f"- Method: `{payload['method']}`",
        f"- Status: `{payload['status']}`",
        f"- Source R28 contract hash: `{summary['source_r28_contract_hash']}`",
        f"- Source R28 template hash: `{summary['source_r28_template_hash']}`",
        f"- Preflight hash: `{summary['preflight_hash']}`",
        "",
        "## Result",
        "",
        (
            f"R29 passes {summary['requirements_passed']}/"
            f"{summary['requirement_count']} requirements by rejecting the R28 "
            "template when it is treated as a placeholder submission."
        ),
        "",
        "## Gate Outcome",
        "",
        f"- Passed gates: `{', '.join(summary['passed_gate_ids'])}`",
        f"- Failed gates: `{', '.join(summary['failed_gate_ids'])}`",
        f"- Placeholder field count: `{summary['placeholder_field_count']}`",
        "",
        "## Requirement Results",
        "",
    ]
    for item in payload["requirements"]:
        mark = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- `{item['requirement_id']}` {mark}: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            "",
            f"- validation_error_count: `{summary['validation_error_count']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--r28-contract",
        type=Path,
        default=Path("results/B1_B7_cone01_R28_o3_f4_certificate_triad_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--template-submission",
        type=Path,
        default=Path(
            "results/B1_B7_cone01_o3_f4_numerical_refit_submissions/"
            "B1-B7-cone01-O3-F4-certificate-triad.template.json"
        ),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B1_B7_cone01_R29_o3_f4_certificate_triad_preflight_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B1_B7_cone01_R29_o3_f4_certificate_triad_preflight_gate.md"),
    )
    parser.add_argument("--pretty", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=True)
    write_markdown(args.markdown_output, payload)
    if args.pretty:
        print(
            json.dumps(
                {
                    "status": payload["status"],
                    "requirements_passed": payload["summary"]["requirements_passed"],
                    "requirements_failed": payload["summary"]["requirements_failed"],
                    "accepted": payload["summary"]["accepted"],
                    "passed_gate_ids": payload["summary"]["passed_gate_ids"],
                    "failed_gate_ids": payload["summary"]["failed_gate_ids"],
                    "placeholder_field_count": payload["summary"]["placeholder_field_count"],
                    "preflight_hash": payload["summary"]["preflight_hash"],
                    "o3_closed": payload["summary"]["o3_closed"],
                    "reroute_allowed": payload["summary"]["reroute_allowed"],
                    "b7_credit_delta": payload["summary"]["b7_credit_delta"],
                    "json_output": str(args.json_output),
                    "markdown_output": str(args.markdown_output),
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
