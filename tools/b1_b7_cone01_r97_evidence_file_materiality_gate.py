#!/usr/bin/env python3
"""T-B1-004gu/T-B7-016d: R97 evidence-file materiality gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r97_evidence_file_materiality_gate_v0"
STATUS = "cone01_r97_evidence_file_materiality_rejects_spoof_transcript"
MODEL_STATUS = "r96_validator_ready_but_file_materiality_required"
VERSION = "0.1"
TARGET_ID = "T-B1-004gu/T-B7-016d"
UPSTREAM_TARGET_ID = "T-B1-004gt/T-B7-016c"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R96_RESULT = "results/B1_B7_cone01_R96_review_transcript_validator_gate_v0.json"
R96_VALIDATOR_RULES = f"{SUBMISSION_DIR}/R96-G1-review-transcript-validator-rules.json"
R96_EMPTY_VALIDATION = (
    f"{SUBMISSION_DIR}/R96-G1-empty-review-transcript-validation.verdict.json"
)
R96_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R96-G1-post-transcript-validator-blocker-queue.json"
R95_TRANSCRIPT_TEMPLATE = f"{SUBMISSION_DIR}/R95-G1-maintainer-review-transcript.template.json"

R97_MATERIALITY_RULES = f"{SUBMISSION_DIR}/R97-G1-evidence-file-materiality-rules.json"
R97_SPOOF_TRANSCRIPT = f"{SUBMISSION_DIR}/R97-G1-spoofed-review-transcript.json"
R97_SPOOF_VALIDATION = (
    f"{SUBMISSION_DIR}/R97-G1-spoofed-review-transcript-materiality.verdict.json"
)
R97_STDOUT = f"{SUBMISSION_DIR}/R97-G1-evidence-file-materiality.stdout.txt"
R97_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R97-G1-post-materiality-blocker-queue.json"

RESULT_PATH = "results/B1_B7_cone01_R97_evidence_file_materiality_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R97_evidence_file_materiality_gate.md"

EVIDENCE_FILE_PAIRS = [
    ("reviewed_r93_packet_path", "reviewed_r93_packet_sha256"),
    ("command_transcript_path", "command_transcript_sha256"),
    ("environment_manifest_path", "environment_manifest_sha256"),
    ("recomputed_target_rows_path", "recomputed_target_rows_sha256"),
    ("double_count_test_path", "double_count_test_sha256"),
    ("review_notes_path", "review_notes_sha256"),
]

SPOOF_DIR = f"{SUBMISSION_DIR}/r97_spoofed_missing_evidence"
FAKE_SHA = "0" * 64


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


def build_materiality_rules(
    root: Path,
    r96_result: dict[str, Any],
    r96_rules: dict[str, Any],
    r96_validation: dict[str, Any],
    r96_blocker_queue: dict[str, Any],
) -> dict[str, Any]:
    rules = {
        "artifact": "R97 G1 evidence-file materiality rules",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r96_result_path": R96_RESULT,
        "source_r96_result_sha256": file_hash(root / R96_RESULT),
        "source_r96_payload_hash": r96_result["payload_hash"],
        "source_r96_validator_rules_path": R96_VALIDATOR_RULES,
        "source_r96_validator_rules_sha256": file_hash(root / R96_VALIDATOR_RULES),
        "source_r96_validator_rules_hash": r96_rules["validator_rules_hash"],
        "source_r96_empty_validation_path": R96_EMPTY_VALIDATION,
        "source_r96_empty_validation_sha256": file_hash(root / R96_EMPTY_VALIDATION),
        "source_r96_empty_validation_hash": r96_validation["validation_hash"],
        "source_r96_blocker_queue_path": R96_BLOCKER_QUEUE,
        "source_r96_blocker_queue_sha256": file_hash(root / R96_BLOCKER_QUEUE),
        "source_r96_blocker_queue_hash": r96_blocker_queue["blocker_queue_hash"],
        "validator_id": "R97-G1-evidence-file-materiality-validator",
        "route_id": r96_rules["route_id"],
        "base_validator_rules_hash": r96_rules["validator_rules_hash"],
        "base_validator_gate_count": len(r96_rules["validator_gates"]),
        "evidence_file_pairs": EVIDENCE_FILE_PAIRS,
        "evidence_file_pair_count": len(EVIDENCE_FILE_PAIRS),
        "materiality_gates": [
            "all_production_fields_present",
            "allowed_labels_and_targets",
            "all_evidence_paths_declared",
            "all_evidence_paths_exist",
            "all_evidence_hashes_match_declared_sha256",
            "reviewed_packet_hash_not_fake",
            "reviewer_signature_not_fake",
            "zero_direct_new_credit",
            "claim_boundary_safe",
            "materiality_validation_accepted",
        ],
        "accepted_fake_sha_values": [],
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
            "R97 hardens R96 by requiring declared review evidence files to exist "
            "and match their SHA-256 claims. A filled-looking spoof transcript with "
            "missing evidence files is rejected and no counter or B7 credit moves."
        ),
    }
    rules["materiality_rules_hash"] = stable_self_hash(rules, "materiality_rules_hash")
    return rules


def build_spoof_transcript(
    r96_rules: dict[str, Any],
    r95_template: dict[str, Any],
    materiality_rules: dict[str, Any],
) -> dict[str, Any]:
    fields = dict(r95_template["fields"])
    fields.update(
        {
            "transcript_id": "R97-G1-spoofed-filled-looking-transcript",
            "reviewer_agent_id": "r97-spoof-reviewer",
            "reviewed_r93_packet_path": f"{SPOOF_DIR}/missing_r93_packet.json",
            "reviewed_r93_packet_sha256": FAKE_SHA,
            "reviewed_r93_packet_hash": FAKE_SHA,
            "source_r94_verdict_contract_hash": r95_template["fields"].get(
                "source_r94_verdict_contract_hash"
            )
            or r96_rules["source_r95_transcript_contract_hash"],
            "source_r94_verdict_template_hash": r95_template["fields"].get(
                "source_r94_verdict_template_hash"
            )
            or r96_rules["source_r95_transcript_template_hash"],
            "command_transcript_path": f"{SPOOF_DIR}/missing_command_transcript.txt",
            "command_transcript_sha256": FAKE_SHA,
            "environment_manifest_path": f"{SPOOF_DIR}/missing_environment.json",
            "environment_manifest_sha256": FAKE_SHA,
            "recomputed_target_rows_path": f"{SPOOF_DIR}/missing_recomputed_rows.json",
            "recomputed_target_rows_sha256": FAKE_SHA,
            "double_count_test_path": f"{SPOOF_DIR}/missing_double_count_test.json",
            "double_count_test_sha256": FAKE_SHA,
            "review_notes_path": f"{SPOOF_DIR}/missing_review_notes.md",
            "review_notes_sha256": FAKE_SHA,
            "evidence_sufficiency_label": "insufficient_evidence_no_counter",
            "counter_target": "no_counter_change",
            "proposed_credit_decision": "insufficient_evidence_no_counter",
            "proposed_counter_delta": 0,
            "one_unit_credit_preserved": False,
            "one_unit_credit_revoked": False,
            "new_credit_delta": 0,
            "claim_boundary": "spoofed_missing_evidence_negative_control_no_counter",
            "o3_closed": False,
            "resource_saving_claimed": False,
            "physical_layout_claimed": False,
            "transcript_timestamp_unix": 0,
            "reviewer_signature_hash": FAKE_SHA,
        }
    )
    transcript = {
        "artifact": "R97 spoofed filled-looking review transcript negative control",
        "contract_id": "R95-G1-maintainer-review-transcript-intake",
        "materiality_rules_hash": materiality_rules["materiality_rules_hash"],
        "base_validator_rules_hash": r96_rules["validator_rules_hash"],
        "fields": fields,
        "negative_control_reason": (
            "All production-style strings are filled, but evidence file paths are "
            "intentionally missing and hashes are fake."
        ),
    }
    transcript["transcript_hash"] = stable_self_hash(transcript, "transcript_hash")
    return transcript


def existing_file_hash(root: Path, rel_path: str) -> str | None:
    path = root / rel_path
    if not path.exists() or not path.is_file():
        return None
    return file_hash(path)


def validate_materiality(
    root: Path,
    rules: dict[str, Any],
    r96_rules: dict[str, Any],
    transcript: dict[str, Any],
) -> dict[str, Any]:
    fields = transcript["fields"]
    production_missing = [
        field for field in r96_rules["production_required_fields"] if fields.get(field) in (None, "")
    ]
    allowed_labels = (
        fields.get("evidence_sufficiency_label") in r96_rules["allowed_evidence_sufficiency"]
        and fields.get("counter_target") in r96_rules["allowed_counter_targets"]
        and fields.get("proposed_credit_decision") in r96_rules["allowed_credit_decisions"]
    )
    evidence_paths = [fields.get(path_key) for path_key, _ in EVIDENCE_FILE_PAIRS]
    evidence_hashes = [fields.get(hash_key) for _, hash_key in EVIDENCE_FILE_PAIRS]
    existence = {
        fields.get(path_key): existing_file_hash(root, fields.get(path_key) or "")
        for path_key, _ in EVIDENCE_FILE_PAIRS
    }
    hash_matches = {}
    for path_key, hash_key in EVIDENCE_FILE_PAIRS:
        rel = fields.get(path_key)
        actual = existence.get(rel)
        declared = fields.get(hash_key)
        hash_matches[rel] = actual is not None and actual == declared
    gates = {
        "all_production_fields_present": not production_missing,
        "allowed_labels_and_targets": allowed_labels,
        "all_evidence_paths_declared": all(bool(path) for path in evidence_paths),
        "all_evidence_paths_exist": all(value is not None for value in existence.values()),
        "all_evidence_hashes_match_declared_sha256": all(hash_matches.values()),
        "reviewed_packet_hash_not_fake": fields.get("reviewed_r93_packet_hash") != FAKE_SHA,
        "reviewer_signature_not_fake": fields.get("reviewer_signature_hash") != FAKE_SHA,
        "zero_direct_new_credit": fields.get("new_credit_delta") == 0
        and fields.get("proposed_counter_delta") == 0,
        "claim_boundary_safe": fields.get("o3_closed") is False
        and fields.get("resource_saving_claimed") is False
        and fields.get("physical_layout_claimed") is False,
        "materiality_validation_accepted": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    validation = {
        "artifact": "R97 spoofed transcript evidence-file materiality validation verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "materiality_rules_hash": rules["materiality_rules_hash"],
        "base_validator_rules_hash": r96_rules["validator_rules_hash"],
        "transcript_hash": transcript["transcript_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "production_missing_fields": production_missing,
        "evidence_path_existence": existence,
        "evidence_hash_matches": hash_matches,
        "fake_sha_value": FAKE_SHA,
        "spoof_transcript_rejected": True,
        "materiality_validation_accepted": False,
        "review_transcript_accepted": False,
        "maintainer_verdict_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "claim_boundary": rules["claim_boundary"],
    }
    validation["materiality_validation_hash"] = stable_self_hash(
        validation, "materiality_validation_hash"
    )
    return validation


def build_blocker_queue(rules: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R97 post evidence-file materiality blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "materiality_rules_hash": rules["materiality_rules_hash"],
        "materiality_validation_hash": validation["materiality_validation_hash"],
        "queue": [
            {
                "blocker_id": "R97-G1-1",
                "priority": 1,
                "target_gate": "real_evidence_file_bundle",
                "needed_artifact": "all declared evidence files must exist inside the repository artifact tree",
            },
            {
                "blocker_id": "R97-G1-2",
                "priority": 2,
                "target_gate": "sha256_materiality_match",
                "needed_artifact": "declared SHA-256 values must match the actual evidence file bytes",
            },
            {
                "blocker_id": "R97-G1-3",
                "priority": 3,
                "target_gate": "nonfake_packet_and_signature_hashes",
                "needed_artifact": "reviewed packet hash and reviewer signature hash must be non-placeholder values",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, rules: dict[str, Any], validation: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R97 evidence-file materiality stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"materiality_rules_hash={rules['materiality_rules_hash']}",
            f"materiality_validation_hash={validation['materiality_validation_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"materiality_gate_count={len(rules['materiality_gates'])}",
            f"failed_gate_count={validation['failed_gate_count']}",
            "spoof_transcript_rejected=true",
            "review_transcript_accepted=false",
            "maintainer_verdict_accepted=false",
            "accepted_external_reproduction_count=0",
            "accepted_external_falsification_count=0",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R97_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r96_result = load_json(root / R96_RESULT)
    r96_rules = load_json(root / R96_VALIDATOR_RULES)
    r96_validation = load_json(root / R96_EMPTY_VALIDATION)
    r96_blocker_queue = load_json(root / R96_BLOCKER_QUEUE)
    r95_template = load_json(root / R95_TRANSCRIPT_TEMPLATE)

    rules = build_materiality_rules(root, r96_result, r96_rules, r96_validation, r96_blocker_queue)
    write_json(root / R97_MATERIALITY_RULES, rules)
    spoof = build_spoof_transcript(r96_rules, r95_template, rules)
    write_json(root / R97_SPOOF_TRANSCRIPT, spoof)
    validation = validate_materiality(root, rules, r96_rules, spoof)
    write_json(root / R97_SPOOF_VALIDATION, validation)
    blocker_queue = build_blocker_queue(rules, validation)
    write_json(root / R97_BLOCKER_QUEUE, blocker_queue)
    stdout_sha256 = write_stdout(root, rules, validation, blocker_queue)

    requirements = [
        req(
            "A1",
            "R97 binds the R96 result, validator rules, empty validation, and blocker queue",
            r96_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r96_result["validator_rules_hash"] == r96_rules["validator_rules_hash"]
            and r96_result["empty_validation_hash"] == r96_validation["validation_hash"]
            and r96_result["blocker_queue_hash"] == r96_blocker_queue["blocker_queue_hash"],
            {
                "r96_payload_hash": r96_result["payload_hash"],
                "r96_validator_rules_hash": r96_rules["validator_rules_hash"],
                "r96_empty_validation_hash": r96_validation["validation_hash"],
            },
        ),
        req(
            "A2",
            "R97 emits materiality rules that require evidence file existence and hash matching",
            len(rules["materiality_gates"]) == 10
            and rules["evidence_file_pair_count"] == 6
            and "all_evidence_paths_exist" in rules["materiality_gates"]
            and "all_evidence_hashes_match_declared_sha256" in rules["materiality_gates"],
            {
                "materiality_rules_hash": rules["materiality_rules_hash"],
                "materiality_gate_count": len(rules["materiality_gates"]),
                "evidence_file_pair_count": rules["evidence_file_pair_count"],
            },
        ),
        req(
            "A3",
            "R97 emits a filled-looking spoof transcript negative control",
            spoof["fields"]["reviewer_agent_id"] == "r97-spoof-reviewer"
            and spoof["fields"]["reviewed_r93_packet_hash"] == FAKE_SHA
            and all(spoof["fields"].get(path_key) for path_key, _ in EVIDENCE_FILE_PAIRS),
            {
                "spoof_transcript_hash": spoof["transcript_hash"],
                "fake_sha_value": FAKE_SHA,
            },
        ),
        req(
            "A4",
            "R97 rejects the spoof transcript on material evidence gates",
            validation["spoof_transcript_rejected"] is True
            and validation["materiality_validation_accepted"] is False
            and validation["failed_gate_count"] == 5
            and "all_evidence_paths_exist" in validation["failed_gates"]
            and "all_evidence_hashes_match_declared_sha256" in validation["failed_gates"],
            {
                "materiality_validation_hash": validation["materiality_validation_hash"],
                "failed_gates": validation["failed_gates"],
            },
        ),
        req(
            "A5",
            "R97 keeps maintainer verdict, external counters, and new credit at zero",
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
            "R97 keeps O3, resource-saving, and physical-layout claims closed",
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
            "R97 emits blockers for real files, SHA-256 materiality, and nonfake hashes",
            [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "real_evidence_file_bundle",
                "sha256_materiality_match",
                "nonfake_packet_and_signature_hashes",
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
        validation_errors.append("one or more R97 requirements failed")
    if validation["materiality_validation_accepted"]:
        validation_errors.append("R97 must not accept the spoof transcript")
    if validation["new_credit_delta"] != 0:
        validation_errors.append("R97 must not grant new credit")

    payload = {
        "artifact": "B1/B7 cone01 R97 evidence-file materiality gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "materiality_rules_path": R97_MATERIALITY_RULES,
        "materiality_rules_hash": rules["materiality_rules_hash"],
        "spoof_transcript_path": R97_SPOOF_TRANSCRIPT,
        "spoof_transcript_hash": spoof["transcript_hash"],
        "materiality_validation_path": R97_SPOOF_VALIDATION,
        "materiality_validation_hash": validation["materiality_validation_hash"],
        "stdout_path": R97_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R97_BLOCKER_QUEUE,
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
            "base_validator_gate_count": rules["base_validator_gate_count"],
            "materiality_gate_count": len(rules["materiality_gates"]),
            "evidence_file_pair_count": rules["evidence_file_pair_count"],
            "spoof_transcript_rejected": validation["spoof_transcript_rejected"],
            "materiality_validation_accepted": validation["materiality_validation_accepted"],
            "review_transcript_accepted": validation["review_transcript_accepted"],
            "maintainer_verdict_accepted": validation["maintainer_verdict_accepted"],
            "materiality_failed_gate_count": validation["failed_gate_count"],
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
            "materiality_rules_hash": rules["materiality_rules_hash"],
            "spoof_transcript_hash": spoof["transcript_hash"],
            "materiality_validation_hash": validation["materiality_validation_hash"],
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
        "# B1/B7 Cone01 R97 Evidence-File Materiality Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R97 hardens the R96 transcript validator by requiring declared evidence",
        "files to exist and match their SHA-256 claims. It emits materiality rules,",
        "a filled-looking spoof transcript, and a validation verdict that rejects",
        "the spoof because its evidence files are missing and hashes are fake.",
        "",
        "## Key Counters",
        "",
        f"- Base validator gates: `{summary['base_validator_gate_count']}`",
        f"- Materiality gates: `{summary['materiality_gate_count']}`",
        f"- Evidence file pairs: `{summary['evidence_file_pair_count']}`",
        f"- Spoof transcript rejected: `{summary['spoof_transcript_rejected']}`",
        f"- Materiality validation accepted: `{summary['materiality_validation_accepted']}`",
        f"- Review transcript accepted: `{summary['review_transcript_accepted']}`",
        f"- Maintainer verdict accepted: `{summary['maintainer_verdict_accepted']}`",
        f"- Failed materiality gates: `{summary['materiality_failed_gate_count']}`",
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
            f"- Materiality rules: `{R97_MATERIALITY_RULES}`",
            f"- Spoof transcript: `{R97_SPOOF_TRANSCRIPT}`",
            f"- Spoof validation verdict: `{R97_SPOOF_VALIDATION}`",
            f"- Stdout: `{R97_STDOUT}`",
            f"- Blocker queue: `{R97_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R97 is a materiality hardening gate. It does not accept a transcript yet,",
            "does not accept a maintainer verdict, does not increment reproduction or",
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
