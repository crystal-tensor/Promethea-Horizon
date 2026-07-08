#!/usr/bin/env python3
"""T-B1-004gt/T-B7-016c: R96 review transcript validator gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r96_review_transcript_validator_gate_v0"
STATUS = "cone01_r96_review_transcript_validator_ready_no_valid_transcript_yet"
MODEL_STATUS = "r95_transcript_contract_ready_but_source_backed_transcript_missing"
VERSION = "0.1"
TARGET_ID = "T-B1-004gt/T-B7-016c"
UPSTREAM_TARGET_ID = "T-B1-004gs/T-B7-016b"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R95_RESULT = "results/B1_B7_cone01_R95_maintainer_review_transcript_intake_gate_v0.json"
R95_TRANSCRIPT_CONTRACT = f"{SUBMISSION_DIR}/R95-G1-maintainer-review-transcript-contract.json"
R95_TRANSCRIPT_TEMPLATE = f"{SUBMISSION_DIR}/R95-G1-maintainer-review-transcript.template.json"
R95_EMPTY_TRANSCRIPT = f"{SUBMISSION_DIR}/R95-G1-empty-maintainer-review-transcript.json"
R95_PREFLIGHT = f"{SUBMISSION_DIR}/R95-G1-maintainer-review-transcript-preflight.verdict.json"
R95_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R95-G1-post-review-transcript-blocker-queue.json"

R96_VALIDATOR_RULES = f"{SUBMISSION_DIR}/R96-G1-review-transcript-validator-rules.json"
R96_EMPTY_VALIDATION = f"{SUBMISSION_DIR}/R96-G1-empty-review-transcript-validation.verdict.json"
R96_STDOUT = f"{SUBMISSION_DIR}/R96-G1-review-transcript-validator.stdout.txt"
R96_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R96-G1-post-transcript-validator-blocker-queue.json"

RESULT_PATH = "results/B1_B7_cone01_R96_review_transcript_validator_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R96_review_transcript_validator_gate.md"


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def stable_self_hash(payload: dict[str, Any], hash_key: str) -> str:
    copy = dict(payload)
    copy.pop(hash_key, None)
    return stable_hash(copy)


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


def build_validator_rules(
    root: Path,
    r95_result: dict[str, Any],
    r95_contract: dict[str, Any],
    r95_template: dict[str, Any],
    r95_preflight: dict[str, Any],
    r95_blocker_queue: dict[str, Any],
) -> dict[str, Any]:
    rules = {
        "artifact": "R96 G1 review transcript validator rules",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r95_result_path": R95_RESULT,
        "source_r95_result_sha256": file_hash(root / R95_RESULT),
        "source_r95_payload_hash": r95_result["payload_hash"],
        "source_r95_transcript_contract_path": R95_TRANSCRIPT_CONTRACT,
        "source_r95_transcript_contract_sha256": file_hash(root / R95_TRANSCRIPT_CONTRACT),
        "source_r95_transcript_contract_hash": r95_contract["transcript_contract_hash"],
        "source_r95_transcript_template_path": R95_TRANSCRIPT_TEMPLATE,
        "source_r95_transcript_template_sha256": file_hash(root / R95_TRANSCRIPT_TEMPLATE),
        "source_r95_transcript_template_hash": r95_template["transcript_template_hash"],
        "source_r95_preflight_path": R95_PREFLIGHT,
        "source_r95_preflight_sha256": file_hash(root / R95_PREFLIGHT),
        "source_r95_preflight_hash": r95_preflight["preflight_hash"],
        "source_r95_blocker_queue_path": R95_BLOCKER_QUEUE,
        "source_r95_blocker_queue_sha256": file_hash(root / R95_BLOCKER_QUEUE),
        "source_r95_blocker_queue_hash": r95_blocker_queue["blocker_queue_hash"],
        "validator_id": "R96-G1-review-transcript-validator",
        "route_id": r95_contract["route_id"],
        "required_fields": r95_contract["required_fields"],
        "required_field_count": r95_contract["required_field_count"],
        "production_required_fields": r95_contract["production_required_fields"],
        "production_required_field_count": r95_contract["production_required_field_count"],
        "required_evidence_files": r95_contract["required_evidence_files"],
        "required_evidence_file_count": len(r95_contract["required_evidence_files"]),
        "allowed_evidence_sufficiency": r95_contract["allowed_evidence_sufficiency"],
        "allowed_counter_targets": r95_contract["allowed_counter_targets"],
        "allowed_credit_decisions": r95_contract["allowed_credit_decisions"],
        "validator_gates": [
            "all_required_fields_present",
            "production_required_fields_present",
            "r95_hashes_bound",
            "reviewer_identity_present",
            "reviewed_r93_packet_bound",
            "command_transcript_bound",
            "environment_manifest_bound",
            "recomputed_rows_bound",
            "double_count_test_bound",
            "review_notes_bound",
            "allowed_evidence_sufficiency",
            "allowed_counter_target",
            "allowed_credit_decision",
            "zero_direct_new_credit",
            "counter_delta_zero_until_verdict",
            "claim_boundary_safe",
            "reviewer_signature_present",
            "review_transcript_accepted",
        ],
        "transcript_accepted": False,
        "maintainer_verdict_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "o3_closed": False,
        "resource_saving_claimed": False,
        "physical_layout_claimed": False,
        "claim_boundary": (
            "R96 makes the R95 review transcript contract runnable as validator "
            "rules. The current empty transcript is rejected and no R94 verdict, "
            "counter movement, or new B7 credit is accepted."
        ),
    }
    rules["validator_rules_hash"] = stable_self_hash(rules, "validator_rules_hash")
    return rules


def validate_transcript(rules: dict[str, Any], transcript: dict[str, Any]) -> dict[str, Any]:
    fields = transcript["fields"]
    missing_required = [field for field in rules["required_fields"] if field not in fields]
    missing_production = [
        field for field in rules["production_required_fields"] if fields.get(field) in (None, "")
    ]
    gates = {
        "all_required_fields_present": not missing_required,
        "production_required_fields_present": not missing_production,
        "r95_hashes_bound": fields.get("source_r94_verdict_contract_hash") is not None
        and transcript.get("transcript_contract_hash") == rules["source_r95_transcript_contract_hash"],
        "reviewer_identity_present": bool(fields.get("reviewer_agent_id")),
        "reviewed_r93_packet_bound": bool(fields.get("reviewed_r93_packet_path"))
        and bool(fields.get("reviewed_r93_packet_sha256"))
        and bool(fields.get("reviewed_r93_packet_hash")),
        "command_transcript_bound": bool(fields.get("command_transcript_path"))
        and bool(fields.get("command_transcript_sha256")),
        "environment_manifest_bound": bool(fields.get("environment_manifest_path"))
        and bool(fields.get("environment_manifest_sha256")),
        "recomputed_rows_bound": bool(fields.get("recomputed_target_rows_path"))
        and bool(fields.get("recomputed_target_rows_sha256")),
        "double_count_test_bound": bool(fields.get("double_count_test_path"))
        and bool(fields.get("double_count_test_sha256")),
        "review_notes_bound": bool(fields.get("review_notes_path"))
        and bool(fields.get("review_notes_sha256")),
        "allowed_evidence_sufficiency": fields.get("evidence_sufficiency_label")
        in rules["allowed_evidence_sufficiency"],
        "allowed_counter_target": fields.get("counter_target") in rules["allowed_counter_targets"],
        "allowed_credit_decision": fields.get("proposed_credit_decision")
        in rules["allowed_credit_decisions"],
        "zero_direct_new_credit": fields.get("new_credit_delta") == 0,
        "counter_delta_zero_until_verdict": fields.get("proposed_counter_delta") == 0,
        "claim_boundary_safe": fields.get("o3_closed") is False
        and fields.get("resource_saving_claimed") is False
        and fields.get("physical_layout_claimed") is False,
        "reviewer_signature_present": bool(fields.get("reviewer_signature_hash")),
        "review_transcript_accepted": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R96 empty review transcript validation verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "validator_rules_hash": rules["validator_rules_hash"],
        "transcript_hash": transcript["transcript_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "missing_required_fields": missing_required,
        "missing_production_fields": missing_production,
        "empty_transcript_rejected": True,
        "review_transcript_accepted": False,
        "maintainer_verdict_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "claim_boundary": rules["claim_boundary"],
    }
    verdict["validation_hash"] = stable_self_hash(verdict, "validation_hash")
    return verdict


def build_blocker_queue(rules: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R96 post transcript validator blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "validator_rules_hash": rules["validator_rules_hash"],
        "validation_hash": validation["validation_hash"],
        "queue": [
            {
                "blocker_id": "R96-G1-1",
                "priority": 1,
                "target_gate": "source_backed_r95_transcript_submission",
                "needed_artifact": "filled R95 transcript that passes all R96 validator gates",
            },
            {
                "blocker_id": "R96-G1-2",
                "priority": 2,
                "target_gate": "independent_reviewer_signature",
                "needed_artifact": "reviewer signature hash and independent reviewer identity",
            },
            {
                "blocker_id": "R96-G1-3",
                "priority": 3,
                "target_gate": "r94_verdict_after_validated_transcript",
                "needed_artifact": "R94 maintainer verdict referencing the accepted R96 validation hash",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, rules: dict[str, Any], validation: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R96 review transcript validator stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"validator_rules_hash={rules['validator_rules_hash']}",
            f"validation_hash={validation['validation_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"validator_gate_count={len(rules['validator_gates'])}",
            f"failed_gate_count={validation['failed_gate_count']}",
            "review_transcript_accepted=false",
            "maintainer_verdict_accepted=false",
            "accepted_external_reproduction_count=0",
            "accepted_external_falsification_count=0",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R96_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r95_result = load_json(root / R95_RESULT)
    r95_contract = load_json(root / R95_TRANSCRIPT_CONTRACT)
    r95_template = load_json(root / R95_TRANSCRIPT_TEMPLATE)
    r95_empty_transcript = load_json(root / R95_EMPTY_TRANSCRIPT)
    r95_preflight = load_json(root / R95_PREFLIGHT)
    r95_blocker_queue = load_json(root / R95_BLOCKER_QUEUE)

    rules = build_validator_rules(
        root, r95_result, r95_contract, r95_template, r95_preflight, r95_blocker_queue
    )
    write_json(root / R96_VALIDATOR_RULES, rules)
    validation = validate_transcript(rules, r95_empty_transcript)
    write_json(root / R96_EMPTY_VALIDATION, validation)
    blocker_queue = build_blocker_queue(rules, validation)
    write_json(root / R96_BLOCKER_QUEUE, blocker_queue)
    stdout_sha256 = write_stdout(root, rules, validation, blocker_queue)

    requirements = [
        req(
            "A1",
            "R96 binds the R95 result, transcript contract, template, preflight, and blocker queue",
            r95_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r95_result["transcript_contract_hash"]
            == r95_contract["transcript_contract_hash"]
            and r95_result["transcript_template_hash"]
            == r95_template["transcript_template_hash"]
            and r95_result["preflight_hash"] == r95_preflight["preflight_hash"],
            {
                "r95_payload_hash": r95_result["payload_hash"],
                "r95_transcript_contract_hash": r95_contract["transcript_contract_hash"],
                "r95_preflight_hash": r95_preflight["preflight_hash"],
                "r95_blocker_queue_hash": r95_blocker_queue["blocker_queue_hash"],
            },
        ),
        req(
            "A2",
            "R96 emits runnable validator rules for the R95 transcript contract",
            rules["required_field_count"] == 30
            and rules["production_required_field_count"] == 18
            and len(rules["validator_gates"]) == 18,
            {
                "validator_rules_hash": rules["validator_rules_hash"],
                "validator_gate_count": len(rules["validator_gates"]),
                "required_field_count": rules["required_field_count"],
            },
        ),
        req(
            "A3",
            "R96 validates the current R95 empty transcript artifact",
            validation["transcript_hash"] == r95_empty_transcript["transcript_hash"]
            and validation["validator_rules_hash"] == rules["validator_rules_hash"],
            {
                "empty_transcript_hash": r95_empty_transcript["transcript_hash"],
                "validation_hash": validation["validation_hash"],
            },
        ),
        req(
            "A4",
            "R96 rejects the empty transcript under validator rules",
            validation["empty_transcript_rejected"] is True
            and validation["review_transcript_accepted"] is False
            and validation["failed_gate_count"] == 13,
            {
                "validation_hash": validation["validation_hash"],
                "failed_gates": validation["failed_gates"],
                "missing_production_field_count": len(validation["missing_production_fields"]),
            },
        ),
        req(
            "A5",
            "R96 keeps maintainer verdict, external counters, and new credit at zero",
            validation["maintainer_verdict_accepted"] is False
            and validation["accepted_external_reproduction_count"] == 0
            and validation["accepted_external_falsification_count"] == 0
            and validation["counter_delta"] == 0
            and validation["new_credit_delta"] == 0,
            {
                "maintainer_verdict_accepted": validation["maintainer_verdict_accepted"],
                "counter_delta": validation["counter_delta"],
                "accepted_external_reproduction_count": validation[
                    "accepted_external_reproduction_count"
                ],
                "accepted_external_falsification_count": validation[
                    "accepted_external_falsification_count"
                ],
                "new_credit_delta": validation["new_credit_delta"],
            },
        ),
        req(
            "A6",
            "R96 keeps O3, resource-saving, and physical-layout claims closed",
            rules["o3_closed"] is False
            and rules["resource_saving_claimed"] is False
            and rules["physical_layout_claimed"] is False,
            {
                "o3_closed": rules["o3_closed"],
                "resource_saving_claimed": rules["resource_saving_claimed"],
                "physical_layout_claimed": rules["physical_layout_claimed"],
            },
        ),
        req(
            "A7",
            "R96 emits blockers for valid transcript submission, independent signature, and R94 verdict",
            [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "source_backed_r95_transcript_submission",
                "independent_reviewer_signature",
                "r94_verdict_after_validated_transcript",
            ],
            {
                "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
                "blocker_ids": [item["blocker_id"] for item in blocker_queue["queue"]],
            },
        ),
    ]

    failed_requirements = [
        requirement["requirement_id"] for requirement in requirements if not requirement["passed"]
    ]
    validation_errors = []
    if failed_requirements:
        validation_errors.append("one or more R96 requirements failed")
    if validation["review_transcript_accepted"]:
        validation_errors.append("R96 must not accept the empty transcript")
    if validation["new_credit_delta"] != 0:
        validation_errors.append("R96 must not grant new credit")

    payload = {
        "artifact": "B1/B7 cone01 R96 review transcript validator gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "validator_rules_path": R96_VALIDATOR_RULES,
        "validator_rules_hash": rules["validator_rules_hash"],
        "empty_validation_path": R96_EMPTY_VALIDATION,
        "empty_validation_hash": validation["validation_hash"],
        "stdout_path": R96_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R96_BLOCKER_QUEUE,
        "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
        "requirement_count": len(requirements),
        "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
        "requirements_failed": len(failed_requirements),
        "failed_requirement_ids": failed_requirements,
        "requirements": requirements,
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "summary": {
            "method": METHOD,
            "status": STATUS,
            "model_status": MODEL_STATUS,
            "source_target_id": TARGET_ID,
            "upstream_target_id": UPSTREAM_TARGET_ID,
            "route_id": rules["route_id"],
            "validator_id": rules["validator_id"],
            "required_field_count": rules["required_field_count"],
            "production_required_field_count": rules["production_required_field_count"],
            "required_evidence_file_count": rules["required_evidence_file_count"],
            "validator_gate_count": len(rules["validator_gates"]),
            "empty_transcript_rejected": validation["empty_transcript_rejected"],
            "review_transcript_accepted": validation["review_transcript_accepted"],
            "maintainer_verdict_accepted": validation["maintainer_verdict_accepted"],
            "validation_failed_gate_count": validation["failed_gate_count"],
            "missing_production_field_count": len(validation["missing_production_fields"]),
            "counter_delta": validation["counter_delta"],
            "accepted_external_reproduction_count": validation[
                "accepted_external_reproduction_count"
            ],
            "accepted_external_falsification_count": validation[
                "accepted_external_falsification_count"
            ],
            "new_credit_delta": validation["new_credit_delta"],
            "o3_closed": rules["o3_closed"],
            "resource_saving_claimed": rules["resource_saving_claimed"],
            "physical_layout_claimed": rules["physical_layout_claimed"],
            "validator_rules_hash": rules["validator_rules_hash"],
            "empty_validation_hash": validation["validation_hash"],
            "stdout_sha256": stdout_sha256,
            "blocker_queue_hash": blocker_queue["blocker_queue_hash"],
            "payload_hash": None,
            "requirements_passed": sum(1 for requirement in requirements if requirement["passed"]),
            "requirements_failed": len(failed_requirements),
            "failed_requirement_ids": failed_requirements,
            "validation_error_count": len(validation_errors),
        },
    }
    payload["payload_hash"] = stable_self_hash(payload, "payload_hash")
    payload["summary"]["payload_hash"] = payload["payload_hash"]
    return payload


def write_report(root: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# B1/B7 Cone01 R96 Review Transcript Validator Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R96 converts the R95 review transcript contract into runnable validator",
        "rules. It validates the current empty R95 transcript artifact and rejects",
        "it before any maintainer verdict, reproduction counter, falsification",
        "counter, or new credit can move.",
        "",
        "## Key Counters",
        "",
        f"- Required fields: `{summary['required_field_count']}`",
        f"- Production-required fields: `{summary['production_required_field_count']}`",
        f"- Required evidence-file classes: `{summary['required_evidence_file_count']}`",
        f"- Validator gates: `{summary['validator_gate_count']}`",
        f"- Empty transcript rejected: `{summary['empty_transcript_rejected']}`",
        f"- Review transcript accepted: `{summary['review_transcript_accepted']}`",
        f"- Maintainer verdict accepted: `{summary['maintainer_verdict_accepted']}`",
        f"- Failed validator gates: `{summary['validation_failed_gate_count']}`",
        f"- Missing production fields: `{summary['missing_production_field_count']}`",
        f"- Counter delta: `{summary['counter_delta']}`",
        f"- Accepted external reproductions: `{summary['accepted_external_reproduction_count']}`",
        f"- Accepted external falsifications: `{summary['accepted_external_falsification_count']}`",
        f"- New credit delta: `{summary['new_credit_delta']}`",
        "",
        "## Requirements",
        "",
    ]
    for requirement in payload["requirements"]:
        status = "PASS" if requirement["passed"] else "FAIL"
        lines.append(f"- `{requirement['requirement_id']}` {status}: {requirement['label']}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- Result JSON: `{RESULT_PATH}`",
            f"- Validator rules: `{R96_VALIDATOR_RULES}`",
            f"- Empty validation verdict: `{R96_EMPTY_VALIDATION}`",
            f"- Stdout: `{R96_STDOUT}`",
            f"- Blocker queue: `{R96_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R96 is a validator gate. It does not accept a transcript yet, does not",
            "accept a maintainer verdict, does not increment reproduction or",
            "falsification counters, does not grant new B7 credit, and does not close",
            "1.25x, O3, physical layout, resource-saving, paper, patent, funding, or",
            "product-readiness claims.",
            "",
        ]
    )
    (root / REPORT_PATH).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    payload = build_payload(args)
    write_json(root / RESULT_PATH, payload)
    write_report(root, payload)
    if args.pretty:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
