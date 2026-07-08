#!/usr/bin/env python3
"""T-B1-004gv/T-B7-016e: R98 placeholder evidence semantic gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r98_placeholder_evidence_semantic_gate_v0"
STATUS = "cone01_r98_placeholder_evidence_rejected_no_semantic_review"
MODEL_STATUS = "r97_materiality_ready_but_substantive_review_evidence_missing"
VERSION = "0.1"
TARGET_ID = "T-B1-004gv/T-B7-016e"
UPSTREAM_TARGET_ID = "T-B1-004gu/T-B7-016d"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R97_RESULT = "results/B1_B7_cone01_R97_evidence_file_materiality_gate_v0.json"
R97_MATERIALITY_RULES = f"{SUBMISSION_DIR}/R97-G1-evidence-file-materiality-rules.json"
R97_SPOOF_VALIDATION = (
    f"{SUBMISSION_DIR}/R97-G1-spoofed-review-transcript-materiality.verdict.json"
)
R97_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R97-G1-post-materiality-blocker-queue.json"
R96_VALIDATOR_RULES = f"{SUBMISSION_DIR}/R96-G1-review-transcript-validator-rules.json"
R95_TRANSCRIPT_TEMPLATE = f"{SUBMISSION_DIR}/R95-G1-maintainer-review-transcript.template.json"

R98_BUNDLE_DIR = f"{SUBMISSION_DIR}/R98-G1-placeholder-evidence-bundle"
R98_BUNDLE_MANIFEST = f"{SUBMISSION_DIR}/R98-G1-placeholder-evidence-bundle-manifest.json"
R98_PLACEHOLDER_TRANSCRIPT = f"{SUBMISSION_DIR}/R98-G1-placeholder-filled-review-transcript.json"
R98_SEMANTIC_VALIDATION = (
    f"{SUBMISSION_DIR}/R98-G1-placeholder-evidence-semantic-validation.verdict.json"
)
R98_STDOUT = f"{SUBMISSION_DIR}/R98-G1-placeholder-evidence-semantic.stdout.txt"
R98_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R98-G1-post-placeholder-semantic-blocker-queue.json"

RESULT_PATH = "results/B1_B7_cone01_R98_placeholder_evidence_semantic_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R98_placeholder_evidence_semantic_gate.md"

EVIDENCE_FILES = {
    "reviewed_r93_packet": "reviewed_r93_packet.json",
    "command_transcript": "command_transcript.txt",
    "environment_manifest": "environment_manifest.json",
    "recomputed_target_rows": "recomputed_target_rows.json",
    "double_count_test": "double_count_test.json",
    "review_notes": "review_notes.md",
}

PLACEHOLDER_MARKER = "R98_PLACEHOLDER_NOT_SUBSTANTIVE"


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


def write_placeholder_files(root: Path) -> dict[str, dict[str, Any]]:
    bundle_dir = root / R98_BUNDLE_DIR
    bundle_dir.mkdir(parents=True, exist_ok=True)
    contents = {
        "reviewed_r93_packet": {
            "placeholder": PLACEHOLDER_MARKER,
            "packet_hash": "placeholder_packet_hash",
            "claim_boundary": "not_a_real_r93_packet",
        },
        "command_transcript": "\n".join(
            [
                PLACEHOLDER_MARKER,
                "No replay command was run.",
                "No stdout or stderr from validator execution is present.",
            ]
        )
        + "\n",
        "environment_manifest": {
            "placeholder": PLACEHOLDER_MARKER,
            "python": "not-recorded",
            "platform": "not-recorded",
        },
        "recomputed_target_rows": {
            "placeholder": PLACEHOLDER_MARKER,
            "rows": [],
            "recomputed": False,
        },
        "double_count_test": {
            "placeholder": PLACEHOLDER_MARKER,
            "double_count_violation_found": None,
            "decision": "not-run",
        },
        "review_notes": "\n".join(
            [
                f"# {PLACEHOLDER_MARKER}",
                "",
                "No substantive review rationale is present.",
                "No independent reproduction or falsification decision is present.",
            ]
        )
        + "\n",
    }
    manifest_entries: dict[str, dict[str, Any]] = {}
    for key, filename in EVIDENCE_FILES.items():
        path = bundle_dir / filename
        content = contents[key]
        if isinstance(content, str):
            path.write_text(content, encoding="utf-8")
        else:
            write_json(path, content)
        rel = f"{R98_BUNDLE_DIR}/{filename}"
        manifest_entries[key] = {
            "path": rel,
            "sha256": file_hash(path),
            "bytes": path.stat().st_size,
            "placeholder_marker": PLACEHOLDER_MARKER,
        }
    return manifest_entries


def build_bundle_manifest(
    root: Path,
    materiality_rules: dict[str, Any],
    evidence_entries: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manifest = {
        "artifact": "R98 G1 placeholder evidence bundle manifest",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r97_materiality_rules_hash": materiality_rules["materiality_rules_hash"],
        "bundle_dir": R98_BUNDLE_DIR,
        "evidence_entries": evidence_entries,
        "evidence_file_count": len(evidence_entries),
        "all_files_exist": all((root / entry["path"]).exists() for entry in evidence_entries.values()),
        "all_hashes_match": all(file_hash(root / entry["path"]) == entry["sha256"] for entry in evidence_entries.values()),
        "semantic_status": "placeholder_negative_control_not_substantive",
    }
    manifest["bundle_manifest_hash"] = stable_self_hash(manifest, "bundle_manifest_hash")
    return manifest


def build_placeholder_transcript(
    r96_rules: dict[str, Any],
    r95_template: dict[str, Any],
    materiality_rules: dict[str, Any],
    bundle_manifest: dict[str, Any],
) -> dict[str, Any]:
    fields = dict(r95_template["fields"])
    entries = bundle_manifest["evidence_entries"]
    fields.update(
        {
            "transcript_id": "R98-G1-placeholder-filled-review-transcript",
            "reviewer_agent_id": "r98-placeholder-reviewer",
            "reviewed_r93_packet_path": entries["reviewed_r93_packet"]["path"],
            "reviewed_r93_packet_sha256": entries["reviewed_r93_packet"]["sha256"],
            "reviewed_r93_packet_hash": "r98-placeholder-packet-hash",
            "source_r94_verdict_contract_hash": r96_rules["source_r95_transcript_contract_hash"],
            "source_r94_verdict_template_hash": r96_rules["source_r95_transcript_template_hash"],
            "command_transcript_path": entries["command_transcript"]["path"],
            "command_transcript_sha256": entries["command_transcript"]["sha256"],
            "environment_manifest_path": entries["environment_manifest"]["path"],
            "environment_manifest_sha256": entries["environment_manifest"]["sha256"],
            "recomputed_target_rows_path": entries["recomputed_target_rows"]["path"],
            "recomputed_target_rows_sha256": entries["recomputed_target_rows"]["sha256"],
            "double_count_test_path": entries["double_count_test"]["path"],
            "double_count_test_sha256": entries["double_count_test"]["sha256"],
            "review_notes_path": entries["review_notes"]["path"],
            "review_notes_sha256": entries["review_notes"]["sha256"],
            "evidence_sufficiency_label": "insufficient_evidence_no_counter",
            "counter_target": "no_counter_change",
            "proposed_credit_decision": "insufficient_evidence_no_counter",
            "proposed_counter_delta": 0,
            "one_unit_credit_preserved": False,
            "one_unit_credit_revoked": False,
            "new_credit_delta": 0,
            "claim_boundary": "placeholder_evidence_negative_control_no_counter",
            "o3_closed": False,
            "resource_saving_claimed": False,
            "physical_layout_claimed": False,
            "transcript_timestamp_unix": 0,
            "reviewer_signature_hash": "r98-placeholder-signature-hash",
        }
    )
    transcript = {
        "artifact": "R98 placeholder filled review transcript negative control",
        "contract_id": "R95-G1-maintainer-review-transcript-intake",
        "materiality_rules_hash": materiality_rules["materiality_rules_hash"],
        "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
        "base_validator_rules_hash": r96_rules["validator_rules_hash"],
        "fields": fields,
        "negative_control_reason": (
            "Evidence files exist and declared hashes match, but the files contain "
            "placeholder content rather than substantive replay, environment, row, "
            "double-count, and review evidence."
        ),
    }
    transcript["transcript_hash"] = stable_self_hash(transcript, "transcript_hash")
    return transcript


def read_text_or_json(root: Path, rel_path: str) -> str:
    path = root / rel_path
    return path.read_text(encoding="utf-8")


def validate_semantics(
    root: Path,
    bundle_manifest: dict[str, Any],
    transcript: dict[str, Any],
) -> dict[str, Any]:
    entries = bundle_manifest["evidence_entries"]
    texts = {key: read_text_or_json(root, entry["path"]) for key, entry in entries.items()}
    all_exist = all((root / entry["path"]).exists() for entry in entries.values())
    all_hash_match = all(
        file_hash(root / entry["path"]) == entry["sha256"] for entry in entries.values()
    )
    no_placeholder_markers = all(PLACEHOLDER_MARKER not in text for text in texts.values())
    command_has_replay = "python3 tools/" in texts["command_transcript"] and "returncode=0" in texts["command_transcript"]
    environment_has_identity = "\"python\"" in texts["environment_manifest"] and "not-recorded" not in texts["environment_manifest"]
    rows_are_recomputed = '"recomputed": true' in texts["recomputed_target_rows"] and '"rows": []' not in texts["recomputed_target_rows"]
    double_count_has_decision = '"double_count_violation_found": false' in texts["double_count_test"]
    notes_have_rationale = "rationale:" in texts["review_notes"].lower() and PLACEHOLDER_MARKER not in texts["review_notes"]
    gates = {
        "all_evidence_files_exist": all_exist,
        "all_declared_hashes_match_file_bytes": all_hash_match,
        "no_placeholder_markers": no_placeholder_markers,
        "command_transcript_has_replay_command": command_has_replay,
        "environment_manifest_has_recorded_identity": environment_has_identity,
        "recomputed_rows_are_nonempty_and_marked_recomputed": rows_are_recomputed,
        "double_count_test_has_explicit_false_decision": double_count_has_decision,
        "review_notes_have_substantive_rationale": notes_have_rationale,
        "zero_direct_new_credit": transcript["fields"]["new_credit_delta"] == 0
        and transcript["fields"]["proposed_counter_delta"] == 0,
        "claim_boundary_safe": transcript["fields"]["o3_closed"] is False
        and transcript["fields"]["resource_saving_claimed"] is False
        and transcript["fields"]["physical_layout_claimed"] is False,
        "semantic_validation_accepted": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    validation = {
        "artifact": "R98 placeholder evidence semantic validation verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
        "transcript_hash": transcript["transcript_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "placeholder_marker": PLACEHOLDER_MARKER,
        "placeholder_transcript_rejected": True,
        "semantic_validation_accepted": False,
        "review_transcript_accepted": False,
        "maintainer_verdict_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "claim_boundary": (
            "R98 rejects evidence files that exist and hash-match but contain only "
            "placeholder content. Real replay commands, environment identity, "
            "recomputed rows, double-count decisions, and review rationale are still missing."
        ),
    }
    validation["semantic_validation_hash"] = stable_self_hash(
        validation, "semantic_validation_hash"
    )
    return validation


def build_blocker_queue(validation: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R98 post placeholder semantic blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "semantic_validation_hash": validation["semantic_validation_hash"],
        "queue": [
            {
                "blocker_id": "R98-G1-1",
                "priority": 1,
                "target_gate": "substantive_command_replay",
                "needed_artifact": "command transcript with actual replay command and returncode 0",
            },
            {
                "blocker_id": "R98-G1-2",
                "priority": 2,
                "target_gate": "nonplaceholder_environment_and_rows",
                "needed_artifact": "environment manifest and recomputed rows with real recorded values",
            },
            {
                "blocker_id": "R98-G1-3",
                "priority": 3,
                "target_gate": "double_count_and_review_rationale",
                "needed_artifact": "explicit double-count decision and substantive review rationale",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, validation: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R98 placeholder evidence semantic stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"semantic_validation_hash={validation['semantic_validation_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"failed_gate_count={validation['failed_gate_count']}",
            "placeholder_transcript_rejected=true",
            "semantic_validation_accepted=false",
            "review_transcript_accepted=false",
            "maintainer_verdict_accepted=false",
            "accepted_external_reproduction_count=0",
            "accepted_external_falsification_count=0",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R98_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r97_result = load_json(root / R97_RESULT)
    r97_rules = load_json(root / R97_MATERIALITY_RULES)
    r97_validation = load_json(root / R97_SPOOF_VALIDATION)
    r97_blocker_queue = load_json(root / R97_BLOCKER_QUEUE)
    r96_rules = load_json(root / R96_VALIDATOR_RULES)
    r95_template = load_json(root / R95_TRANSCRIPT_TEMPLATE)

    evidence_entries = write_placeholder_files(root)
    bundle_manifest = build_bundle_manifest(root, r97_rules, evidence_entries)
    write_json(root / R98_BUNDLE_MANIFEST, bundle_manifest)
    transcript = build_placeholder_transcript(r96_rules, r95_template, r97_rules, bundle_manifest)
    write_json(root / R98_PLACEHOLDER_TRANSCRIPT, transcript)
    validation = validate_semantics(root, bundle_manifest, transcript)
    write_json(root / R98_SEMANTIC_VALIDATION, validation)
    blocker_queue = build_blocker_queue(validation)
    write_json(root / R98_BLOCKER_QUEUE, blocker_queue)
    stdout_sha256 = write_stdout(root, validation, blocker_queue)

    requirements = [
        req(
            "A1",
            "R98 binds the R97 result, materiality rules, spoof validation, and blocker queue",
            r97_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r97_result["materiality_rules_hash"] == r97_rules["materiality_rules_hash"]
            and r97_result["materiality_validation_hash"]
            == r97_validation["materiality_validation_hash"]
            and r97_result["blocker_queue_hash"] == r97_blocker_queue["blocker_queue_hash"],
            {
                "r97_payload_hash": r97_result["payload_hash"],
                "r97_materiality_rules_hash": r97_rules["materiality_rules_hash"],
                "r97_materiality_validation_hash": r97_validation["materiality_validation_hash"],
            },
        ),
        req(
            "A2",
            "R98 emits a real placeholder evidence bundle with files whose hashes match",
            bundle_manifest["evidence_file_count"] == 6
            and bundle_manifest["all_files_exist"] is True
            and bundle_manifest["all_hashes_match"] is True,
            {
                "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
                "evidence_file_count": bundle_manifest["evidence_file_count"],
            },
        ),
        req(
            "A3",
            "R98 emits a filled-looking transcript bound to the placeholder bundle",
            transcript["bundle_manifest_hash"] == bundle_manifest["bundle_manifest_hash"]
            and transcript["fields"]["reviewer_agent_id"] == "r98-placeholder-reviewer",
            {
                "placeholder_transcript_hash": transcript["transcript_hash"],
                "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
            },
        ),
        req(
            "A4",
            "R98 rejects placeholder evidence even though files exist and hashes match",
            validation["placeholder_transcript_rejected"] is True
            and validation["semantic_validation_accepted"] is False
            and validation["failed_gate_count"] == 7
            and "no_placeholder_markers" in validation["failed_gates"]
            and "command_transcript_has_replay_command" in validation["failed_gates"],
            {
                "semantic_validation_hash": validation["semantic_validation_hash"],
                "failed_gates": validation["failed_gates"],
            },
        ),
        req(
            "A5",
            "R98 keeps maintainer verdict, external counters, and new credit at zero",
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
            "R98 keeps O3, resource-saving, and physical-layout claims closed",
            transcript["fields"]["o3_closed"] is False
            and transcript["fields"]["resource_saving_claimed"] is False
            and transcript["fields"]["physical_layout_claimed"] is False,
            {
                "o3_closed": transcript["fields"]["o3_closed"],
                "resource_saving_claimed": transcript["fields"]["resource_saving_claimed"],
                "physical_layout_claimed": transcript["fields"]["physical_layout_claimed"],
            },
        ),
        req(
            "A7",
            "R98 emits blockers for substantive replay, environment/rows, and review rationale",
            [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "substantive_command_replay",
                "nonplaceholder_environment_and_rows",
                "double_count_and_review_rationale",
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
        validation_errors.append("one or more R98 requirements failed")
    if validation["semantic_validation_accepted"]:
        validation_errors.append("R98 must not accept placeholder evidence")
    if validation["new_credit_delta"] != 0:
        validation_errors.append("R98 must not grant new credit")

    payload = {
        "artifact": "B1/B7 cone01 R98 placeholder evidence semantic gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "bundle_manifest_path": R98_BUNDLE_MANIFEST,
        "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
        "placeholder_transcript_path": R98_PLACEHOLDER_TRANSCRIPT,
        "placeholder_transcript_hash": transcript["transcript_hash"],
        "semantic_validation_path": R98_SEMANTIC_VALIDATION,
        "semantic_validation_hash": validation["semantic_validation_hash"],
        "stdout_path": R98_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R98_BLOCKER_QUEUE,
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
            "evidence_file_count": bundle_manifest["evidence_file_count"],
            "all_files_exist": bundle_manifest["all_files_exist"],
            "all_hashes_match": bundle_manifest["all_hashes_match"],
            "placeholder_transcript_rejected": validation["placeholder_transcript_rejected"],
            "semantic_validation_accepted": validation["semantic_validation_accepted"],
            "review_transcript_accepted": validation["review_transcript_accepted"],
            "maintainer_verdict_accepted": validation["maintainer_verdict_accepted"],
            "semantic_failed_gate_count": validation["failed_gate_count"],
            "counter_delta": validation["counter_delta"],
            "accepted_external_reproduction_count": validation[
                "accepted_external_reproduction_count"
            ],
            "accepted_external_falsification_count": validation[
                "accepted_external_falsification_count"
            ],
            "new_credit_delta": validation["new_credit_delta"],
            "o3_closed": transcript["fields"]["o3_closed"],
            "resource_saving_claimed": transcript["fields"]["resource_saving_claimed"],
            "physical_layout_claimed": transcript["fields"]["physical_layout_claimed"],
            "bundle_manifest_hash": bundle_manifest["bundle_manifest_hash"],
            "placeholder_transcript_hash": transcript["transcript_hash"],
            "semantic_validation_hash": validation["semantic_validation_hash"],
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
        "# B1/B7 Cone01 R98 Placeholder Evidence Semantic Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R98 hardens R97 by showing that file existence and SHA-256 materiality are",
        "necessary but not sufficient. It creates six real placeholder evidence files,",
        "builds a transcript whose declared hashes match those files, and rejects the",
        "transcript because the file contents are not substantive review evidence.",
        "",
        "## Key Counters",
        "",
        f"- Evidence files: `{summary['evidence_file_count']}`",
        f"- Files exist: `{summary['all_files_exist']}`",
        f"- Hashes match: `{summary['all_hashes_match']}`",
        f"- Placeholder transcript rejected: `{summary['placeholder_transcript_rejected']}`",
        f"- Semantic validation accepted: `{summary['semantic_validation_accepted']}`",
        f"- Review transcript accepted: `{summary['review_transcript_accepted']}`",
        f"- Maintainer verdict accepted: `{summary['maintainer_verdict_accepted']}`",
        f"- Failed semantic gates: `{summary['semantic_failed_gate_count']}`",
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
            f"- Bundle manifest: `{R98_BUNDLE_MANIFEST}`",
            f"- Placeholder transcript: `{R98_PLACEHOLDER_TRANSCRIPT}`",
            f"- Semantic validation verdict: `{R98_SEMANTIC_VALIDATION}`",
            f"- Stdout: `{R98_STDOUT}`",
            f"- Blocker queue: `{R98_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R98 is a semantic hardening gate. It does not accept a transcript yet,",
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
