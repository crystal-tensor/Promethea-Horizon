#!/usr/bin/env python3
"""T-B1-004hb/T-B7-016k: R104 external-origin attestation contract gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r104_external_origin_attestation_contract_gate_v0"
STATUS = "cone01_r104_external_origin_attestation_contract_ready_no_counter_move"
MODEL_STATUS = "r103_rejected_counter_packet_until_origin_attestation_and_nonlocal_replay_exist"
VERSION = "0.1"
TARGET_ID = "T-B1-004hb/T-B7-016k"
UPSTREAM_TARGET_ID = "T-B1-004ha/T-B7-016j"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"

R103_RESULT = "results/B1_B7_cone01_R103_external_counter_transition_audit_gate_v0.json"
R103_AUDIT = f"{SUBMISSION_DIR}/R103-G1-external-counter-transition-audit.verdict.json"
R103_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R103-G1-post-counter-transition-audit-blocker-queue.json"
R101_MANIFEST = f"{SUBMISSION_DIR}/R101-G1-clean-clone-rerun-manifest.json"
R101_TRANSCRIPT = f"{SUBMISSION_DIR}/R101-G1-clean-clone-rerun-transcript.txt"
R103_CLAIMED_DECISION = f"{SUBMISSION_DIR}/R103-G1-claimed-external-counter-decision.json"

R104_ORIGIN_CONTRACT = f"{SUBMISSION_DIR}/R104-G1-external-origin-attestation-contract.json"
R104_ATTESTATION_TEMPLATE = f"{SUBMISSION_DIR}/R104-G1-external-origin-attestation.template.json"
R104_LOCAL_PLACEHOLDER = f"{SUBMISSION_DIR}/R104-G1-local-placeholder-origin-attestation.json"
R104_PREFLIGHT = f"{SUBMISSION_DIR}/R104-G1-external-origin-attestation-preflight.verdict.json"
R104_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R104-G1-post-origin-attestation-contract-blocker-queue.json"
R104_STDOUT = f"{SUBMISSION_DIR}/R104-G1-external-origin-attestation-contract.stdout.txt"

RESULT_PATH = "results/B1_B7_cone01_R104_external_origin_attestation_contract_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R104_external_origin_attestation_contract_gate.md"


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


def build_origin_contract(r103_result: dict[str, Any], r103_audit: dict[str, Any]) -> dict[str, Any]:
    required_fields = [
        "reviewer_id",
        "reviewer_public_contact_or_handle",
        "reviewer_independence_statement",
        "nonmaintainer_execution_context",
        "external_origin_attestation_statement",
        "repository_source_url",
        "repository_source_commit_sha",
        "clone_command",
        "clone_network_transcript_path",
        "clone_network_transcript_sha256",
        "environment_manifest_path",
        "environment_manifest_sha256",
        "replay_artifact_bundle_path",
        "replay_artifact_bundle_sha256",
        "artifact_origin_statement",
        "r103_audit_hash",
        "requested_counter_transition",
        "double_count_prevention_statement",
        "claim_boundary",
        "signature_hash",
    ]
    contract = {
        "artifact": "R104 external-origin attestation contract",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "source_r103_payload_hash": r103_result["payload_hash"],
        "source_r103_audit_hash": r103_audit["audit_hash"],
        "required_fields": required_fields,
        "required_field_count": len(required_fields),
        "forbidden_local_origin_markers": [
            "file://",
            "/tmp/",
            "/Users/",
            "git clone --local",
            "repo-local",
            "R101-G1-clean-clone-rerun",
        ],
        "minimum_nonlocal_artifacts": [
            "clone_network_transcript",
            "environment_manifest",
            "replay_artifact_bundle",
        ],
        "accepted_counter_transition_modes": [
            "external_reproduction_counter_increment",
            "external_falsification_counter_increment",
        ],
        "forbidden_direct_claims": [
            "B7 resource saving",
            "O3 closure",
            "physical layout improvement",
            "1.25x target closure",
        ],
    }
    contract["origin_contract_hash"] = stable_self_hash(contract, "origin_contract_hash")
    return contract


def build_template(contract: dict[str, Any]) -> dict[str, Any]:
    template = {
        "artifact": "R104 external-origin attestation template",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "origin_contract_hash": contract["origin_contract_hash"],
        "instructions": [
            "Fill every field with externally produced evidence.",
            "Do not reuse R101 local-clean-clone artifacts as external-origin evidence.",
            "Attach a network-visible clone transcript and environment manifest.",
            "Request exactly one reproduction or falsification counter transition.",
        ],
        "fields": {field: "" for field in contract["required_fields"]},
    }
    template["attestation_template_hash"] = stable_self_hash(
        template, "attestation_template_hash"
    )
    return template


def build_local_placeholder(
    root: Path,
    contract: dict[str, Any],
    r103_audit: dict[str, Any],
) -> dict[str, Any]:
    fields = {
        "reviewer_id": "local-placeholder-r104",
        "reviewer_public_contact_or_handle": "maintainer-local-placeholder",
        "reviewer_independence_statement": "claims_independent_but_no_external_origin_attestation",
        "nonmaintainer_execution_context": "false_local_maintainer_context",
        "external_origin_attestation_statement": "not_external_origin_attested",
        "repository_source_url": "file:///tmp/prometheus-r77-dcCJMU/repo",
        "repository_source_commit_sha": "local_worktree_current_head",
        "clone_command": "git clone --local /tmp/prometheus-r77-dcCJMU/repo /tmp/r104-placeholder",
        "clone_network_transcript_path": R101_TRANSCRIPT,
        "clone_network_transcript_sha256": file_hash(root / R101_TRANSCRIPT),
        "environment_manifest_path": R101_MANIFEST,
        "environment_manifest_sha256": file_hash(root / R101_MANIFEST),
        "replay_artifact_bundle_path": R103_CLAIMED_DECISION,
        "replay_artifact_bundle_sha256": file_hash(root / R103_CLAIMED_DECISION),
        "artifact_origin_statement": "repo-local artifact reuse from R101 and R103",
        "r103_audit_hash": r103_audit["audit_hash"],
        "requested_counter_transition": "external_reproduction_counter_increment",
        "double_count_prevention_statement": "not_proven_nonduplicate_external_replay",
        "claim_boundary": (
            "This placeholder is a negative control. It must not be accepted as "
            "external-origin evidence or as an external counter transition."
        ),
    }
    fields["signature_hash"] = stable_hash(
        {
            "reviewer_id": fields["reviewer_id"],
            "repository_source_url": fields["repository_source_url"],
            "clone_network_transcript_sha256": fields["clone_network_transcript_sha256"],
            "environment_manifest_sha256": fields["environment_manifest_sha256"],
            "r103_audit_hash": fields["r103_audit_hash"],
        }
    )
    placeholder = {
        "artifact": "R104 local placeholder external-origin attestation negative control",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "origin_contract_hash": contract["origin_contract_hash"],
        "fields": fields,
        "negative_control_reason": (
            "The attestation is structurally filled, but every origin signal is local "
            "or self-referential."
        ),
    }
    placeholder["local_placeholder_hash"] = stable_self_hash(
        placeholder, "local_placeholder_hash"
    )
    return placeholder


def contains_forbidden_marker(value: str, markers: list[str]) -> bool:
    return any(marker in value for marker in markers)


def build_preflight(
    root: Path,
    contract: dict[str, Any],
    template: dict[str, Any],
    placeholder: dict[str, Any],
    r103_audit: dict[str, Any],
) -> dict[str, Any]:
    fields = placeholder["fields"]
    missing = [field for field in contract["required_fields"] if fields.get(field) in (None, "")]
    markers = contract["forbidden_local_origin_markers"]
    env_path = root / fields["environment_manifest_path"]
    transcript_path = root / fields["clone_network_transcript_path"]
    replay_path = root / fields["replay_artifact_bundle_path"]
    env_manifest = load_json(env_path) if env_path.exists() else {}
    transcript_text = transcript_path.read_text(encoding="utf-8") if transcript_path.exists() else ""
    source_url_nonlocal = not contains_forbidden_marker(fields["repository_source_url"], markers)
    clone_command_nonlocal = not contains_forbidden_marker(fields["clone_command"], markers)
    transcript_nonlocal = (
        transcript_path.exists()
        and file_hash(transcript_path) == fields["clone_network_transcript_sha256"]
        and not contains_forbidden_marker(transcript_text, markers)
    )
    environment_nonlocal = (
        env_path.exists()
        and file_hash(env_path) == fields["environment_manifest_sha256"]
        and env_manifest.get("clone_was_local") is not True
        and not contains_forbidden_marker(fields["environment_manifest_path"], markers)
    )
    replay_bundle_nonlocal = (
        replay_path.exists()
        and file_hash(replay_path) == fields["replay_artifact_bundle_sha256"]
        and "repo-local" not in fields["artifact_origin_statement"]
        and not contains_forbidden_marker(fields["replay_artifact_bundle_path"], markers)
    )
    signed_origin_statement = (
        "external_origin_attested" in fields["external_origin_attestation_statement"]
        and "not_" not in fields["external_origin_attestation_statement"]
        and fields["signature_hash"] != ""
    )
    accepted_counter_mode = (
        fields["requested_counter_transition"] in contract["accepted_counter_transition_modes"]
    )
    gates = {
        "r104_contract_bound_to_r103": r103_audit["audit_hash"]
        == contract["source_r103_audit_hash"]
        == fields["r103_audit_hash"],
        "template_bound_to_contract": template["origin_contract_hash"]
        == contract["origin_contract_hash"],
        "all_required_fields_present": not missing,
        "accepted_counter_transition_mode_requested": accepted_counter_mode,
        "signature_hash_present": fields["signature_hash"] != "",
        "source_url_nonlocal": source_url_nonlocal,
        "clone_command_nonlocal": clone_command_nonlocal,
        "transcript_nonlocal": transcript_nonlocal,
        "environment_manifest_nonlocal": environment_nonlocal,
        "replay_bundle_nonlocal": replay_bundle_nonlocal,
        "signed_external_origin_statement": signed_origin_statement,
        "origin_attestation_accepted": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    preflight = {
        "artifact": "R104 external-origin attestation preflight verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "origin_contract_hash": contract["origin_contract_hash"],
        "attestation_template_hash": template["attestation_template_hash"],
        "local_placeholder_hash": placeholder["local_placeholder_hash"],
        "source_r103_audit_hash": r103_audit["audit_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "local_placeholder_rejected": True,
        "origin_attestation_accepted": False,
        "counter_transition_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "rejection_reason": "local_placeholder_lacks_external_origin_and_nonlocal_replay_artifacts",
        "claim_boundary": (
            "R104 defines the external-origin attestation intake contract and rejects "
            "a local placeholder. It does not accept any external counter transition."
        ),
    }
    preflight["preflight_hash"] = stable_self_hash(preflight, "preflight_hash")
    return preflight


def build_blocker_queue(preflight: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R104 post external-origin attestation blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "preflight_hash": preflight["preflight_hash"],
        "queue": [
            {
                "blocker_id": "R104-G1-1",
                "priority": 1,
                "target_gate": "signed_external_origin_attestation",
                "needed_artifact": "reviewer identity, independence statement, and signed external-origin attestation",
            },
            {
                "blocker_id": "R104-G1-2",
                "priority": 2,
                "target_gate": "nonlocal_clean_checkout_bundle",
                "needed_artifact": "network-visible clone transcript, environment manifest, and replay bundle not sourced from R101/R103 local files",
            },
            {
                "blocker_id": "R104-G1-3",
                "priority": 3,
                "target_gate": "accepted_single_counter_transition_audit",
                "needed_artifact": "audit accepting exactly one reproduction or falsification counter transition",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    return queue


def write_stdout(root: Path, preflight: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R104 external-origin attestation contract stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"preflight_hash={preflight['preflight_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"passed_gate_count={preflight['passed_gate_count']}",
            f"failed_gate_count={preflight['failed_gate_count']}",
            "local_placeholder_rejected=true",
            "origin_attestation_accepted=false",
            "counter_transition_accepted=false",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R104_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r103_result = load_json(root / R103_RESULT)
    r103_audit = load_json(root / R103_AUDIT)
    r103_queue = load_json(root / R103_BLOCKER_QUEUE)
    contract = build_origin_contract(r103_result, r103_audit)
    write_json(root / R104_ORIGIN_CONTRACT, contract)
    template = build_template(contract)
    write_json(root / R104_ATTESTATION_TEMPLATE, template)
    placeholder = build_local_placeholder(root, contract, r103_audit)
    write_json(root / R104_LOCAL_PLACEHOLDER, placeholder)
    preflight = build_preflight(root, contract, template, placeholder, r103_audit)
    write_json(root / R104_PREFLIGHT, preflight)
    blocker_queue = build_blocker_queue(preflight)
    write_json(root / R104_BLOCKER_QUEUE, blocker_queue)
    stdout_sha256 = write_stdout(root, preflight, blocker_queue)

    requirements = [
        req(
            "A1",
            "R104 binds the R103 audit verdict and blocker queue",
            r103_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r103_result["audit_hash"] == r103_audit["audit_hash"]
            and r103_result["blocker_queue_hash"] == r103_queue["blocker_queue_hash"]
            and [item["target_gate"] for item in r103_queue["queue"]]
            == [
                "external_origin_attestation",
                "nonlocal_replay_artifacts",
                "accepted_single_counter_transition",
            ],
            {
                "r103_payload_hash": r103_result["payload_hash"],
                "r103_audit_hash": r103_audit["audit_hash"],
                "r103_blocker_queue_hash": r103_queue["blocker_queue_hash"],
            },
        ),
        req(
            "A2",
            "R104 emits the external-origin attestation contract and template",
            contract["required_field_count"] == 20
            and template["origin_contract_hash"] == contract["origin_contract_hash"],
            {
                "origin_contract_hash": contract["origin_contract_hash"],
                "attestation_template_hash": template["attestation_template_hash"],
                "required_field_count": contract["required_field_count"],
            },
        ),
        req(
            "A3",
            "R104 rejects the local placeholder origin attestation",
            preflight["local_placeholder_rejected"] is True
            and preflight["origin_attestation_accepted"] is False
            and "source_url_nonlocal" in preflight["failed_gates"]
            and "clone_command_nonlocal" in preflight["failed_gates"]
            and "environment_manifest_nonlocal" in preflight["failed_gates"]
            and "transcript_nonlocal" in preflight["failed_gates"],
            {"preflight_hash": preflight["preflight_hash"], "failed_gates": preflight["failed_gates"]},
        ),
        req(
            "A4",
            "R104 keeps counters and new credit at zero",
            preflight["counter_delta"] == 0
            and preflight["accepted_external_reproduction_count"] == 0
            and preflight["accepted_external_falsification_count"] == 0
            and preflight["new_credit_delta"] == 0,
            {
                "counter_delta": preflight["counter_delta"],
                "accepted_external_reproduction_count": preflight[
                    "accepted_external_reproduction_count"
                ],
                "accepted_external_falsification_count": preflight[
                    "accepted_external_falsification_count"
                ],
                "new_credit_delta": preflight["new_credit_delta"],
            },
        ),
        req(
            "A5",
            "R104 emits blockers for signed origin, nonlocal bundle, and single-counter audit",
            [item["target_gate"] for item in blocker_queue["queue"]]
            == [
                "signed_external_origin_attestation",
                "nonlocal_clean_checkout_bundle",
                "accepted_single_counter_transition_audit",
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
        validation_errors.append("one or more R104 requirements failed")
    if preflight["origin_attestation_accepted"]:
        validation_errors.append("R104 must reject the local placeholder attestation")

    payload = {
        "artifact": "B1/B7 cone01 R104 external-origin attestation contract gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "origin_contract_path": R104_ORIGIN_CONTRACT,
        "origin_contract_hash": contract["origin_contract_hash"],
        "attestation_template_path": R104_ATTESTATION_TEMPLATE,
        "attestation_template_hash": template["attestation_template_hash"],
        "local_placeholder_path": R104_LOCAL_PLACEHOLDER,
        "local_placeholder_hash": placeholder["local_placeholder_hash"],
        "preflight_path": R104_PREFLIGHT,
        "preflight_hash": preflight["preflight_hash"],
        "stdout_path": R104_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R104_BLOCKER_QUEUE,
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
            "required_field_count": contract["required_field_count"],
            "local_placeholder_rejected": preflight["local_placeholder_rejected"],
            "origin_attestation_accepted": preflight["origin_attestation_accepted"],
            "counter_transition_accepted": preflight["counter_transition_accepted"],
            "passed_gate_count": preflight["passed_gate_count"],
            "failed_gate_count": preflight["failed_gate_count"],
            "counter_delta": preflight["counter_delta"],
            "accepted_external_reproduction_count": preflight[
                "accepted_external_reproduction_count"
            ],
            "accepted_external_falsification_count": preflight[
                "accepted_external_falsification_count"
            ],
            "new_credit_delta": preflight["new_credit_delta"],
            "origin_contract_hash": contract["origin_contract_hash"],
            "attestation_template_hash": template["attestation_template_hash"],
            "local_placeholder_hash": placeholder["local_placeholder_hash"],
            "preflight_hash": preflight["preflight_hash"],
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
        "# B1/B7 Cone01 R104 External-Origin Attestation Contract Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R104 turns the R103 origin blocker into a concrete external-origin",
        "attestation contract. It emits a fillable template and rejects a local",
        "placeholder that reuses R101/R103 local artifacts.",
        "",
        "## Key Counters",
        "",
        f"- Required attestation fields: `{summary['required_field_count']}`",
        f"- Local placeholder rejected: `{summary['local_placeholder_rejected']}`",
        f"- Origin attestation accepted: `{summary['origin_attestation_accepted']}`",
        f"- Counter transition accepted: `{summary['counter_transition_accepted']}`",
        f"- Gates passed / failed: `{summary['passed_gate_count']}` / `{summary['failed_gate_count']}`",
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
            f"- Origin contract: `{R104_ORIGIN_CONTRACT}`",
            f"- Attestation template: `{R104_ATTESTATION_TEMPLATE}`",
            f"- Local placeholder: `{R104_LOCAL_PLACEHOLDER}`",
            f"- Preflight verdict: `{R104_PREFLIGHT}`",
            f"- Blocker queue: `{R104_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R104 is an intake-contract gate. It does not prove external origin,",
            "does not accept a counter transition, does not grant new credit, and",
            "does not close B7/O3/resource/layout claims.",
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
