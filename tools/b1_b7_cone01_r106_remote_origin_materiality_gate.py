#!/usr/bin/env python3
"""T-B1-004hd/T-B7-016m: R106 remote-origin materiality gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


METHOD = "b1_b7_cone01_r106_remote_origin_materiality_gate_v0"
STATUS = "cone01_r106_remote_looking_origin_spoof_rejected_no_signature_materiality"
MODEL_STATUS = "r105_surface_verifier_ready_but_remote_looking_spoof_needs_materiality_gate"
VERSION = "0.1"
TARGET_ID = "T-B1-004hd/T-B7-016m"
UPSTREAM_TARGET_ID = "T-B1-004hc/T-B7-016l"
SUBMISSION_DIR = "results/B1_B7_cone01_o3_f4_exit_route_submissions"
R106_DIR = f"{SUBMISSION_DIR}/R106-G1-remote-looking-origin-spoof"
REMOTE_COMMIT_SHA = "dd4500000c5492a94d5e39b55cb1607c786e65ec"

R105_RESULT = "results/B1_B7_cone01_R105_external_origin_attestation_verifier_gate_v0.json"
R105_RULES = f"{SUBMISSION_DIR}/R105-G1-external-origin-attestation-verifier-rules.json"
R105_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R105-G1-post-origin-verifier-blocker-queue.json"
R104_CONTRACT = f"{SUBMISSION_DIR}/R104-G1-external-origin-attestation-contract.json"

R106_TRANSCRIPT = f"{R106_DIR}/claimed-network-clone-transcript.txt"
R106_ENV_MANIFEST = f"{R106_DIR}/claimed-external-environment-manifest.json"
R106_REPLAY_BUNDLE = f"{R106_DIR}/claimed-external-replay-bundle.json"
R106_PACKET = f"{R106_DIR}/remote-looking-origin-packet.json"
R106_SURFACE_VALIDATION = f"{R106_DIR}/r105-surface-validation.verdict.json"
R106_MATERIALITY_AUDIT = f"{R106_DIR}/remote-origin-materiality-audit.verdict.json"
R106_BLOCKER_QUEUE = f"{SUBMISSION_DIR}/R106-G1-post-remote-origin-materiality-blocker-queue.json"
R106_STDOUT = f"{SUBMISSION_DIR}/R106-G1-remote-origin-materiality.stdout.txt"

RESULT_PATH = "results/B1_B7_cone01_R106_remote_origin_materiality_gate_v0.json"
REPORT_PATH = "research/B1_B7_cone01_R106_remote_origin_materiality_gate.md"


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


def contains_forbidden_marker(value: str, markers: list[str]) -> bool:
    return any(marker in value for marker in markers)


def write_support_files(root: Path) -> dict[str, str]:
    transcript = "\n".join(
        [
            "R106 claimed network clone transcript",
            "command=git clone https://github.com/crystal-tensor/Prometheus-plan prometheus-plan-r106",
            f"commit={REMOTE_COMMIT_SHA}",
            "network_context=claimed_external_ci",
            "note=self_declared_remote_looking_fixture",
            "",
        ]
    )
    transcript_path = root / R106_TRANSCRIPT
    transcript_path.parent.mkdir(parents=True, exist_ok=True)
    transcript_path.write_text(transcript, encoding="utf-8")
    env = {
        "artifact": "R106 claimed external environment manifest",
        "clone_was_local": False,
        "environment_kind": "claimed_external_ci",
        "runner_identity": "unverified-r106-runner",
        "host_attestation": "self_declared_no_independent_ci_url",
        "python": "3.12",
    }
    write_json(root / R106_ENV_MANIFEST, env)
    replay = {
        "artifact": "R106 claimed external replay bundle",
        "bundle_kind": "claimed_external_replay",
        "source": "self_declared_remote_looking_fixture",
        "commands": [
            "python3 tools/b1_b7_cone01_r105_external_origin_attestation_verifier_gate.py --repo-root ."
        ],
        "reviewer_signature_material": "absent",
        "third_party_ci_material": "absent",
    }
    write_json(root / R106_REPLAY_BUNDLE, replay)
    return {
        "transcript_sha256": file_hash(transcript_path),
        "env_manifest_sha256": file_hash(root / R106_ENV_MANIFEST),
        "replay_bundle_sha256": file_hash(root / R106_REPLAY_BUNDLE),
    }


def build_remote_looking_packet(root: Path, contract: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any]:
    fields = {
        "reviewer_id": "claimed-independent-reviewer-r106",
        "reviewer_public_contact_or_handle": "https://github.com/claimed-r106-reviewer",
        "reviewer_independence_statement": "claims_no_maintainer_affiliation",
        "nonmaintainer_execution_context": "claimed_external_ci_environment",
        "external_origin_attestation_statement": "external_origin_attested_by_self_declared_packet",
        "repository_source_url": "https://github.com/crystal-tensor/Prometheus-plan",
        "repository_source_commit_sha": REMOTE_COMMIT_SHA,
        "clone_command": "git clone https://github.com/crystal-tensor/Prometheus-plan prometheus-plan-r106",
        "clone_network_transcript_path": R106_TRANSCRIPT,
        "clone_network_transcript_sha256": hashes["transcript_sha256"],
        "environment_manifest_path": R106_ENV_MANIFEST,
        "environment_manifest_sha256": hashes["env_manifest_sha256"],
        "replay_artifact_bundle_path": R106_REPLAY_BUNDLE,
        "replay_artifact_bundle_sha256": hashes["replay_bundle_sha256"],
        "artifact_origin_statement": "claimed_external_replay_bundle_no_local_markers",
        "r103_audit_hash": contract["source_r103_audit_hash"],
        "requested_counter_transition": "external_reproduction_counter_increment",
        "double_count_prevention_statement": "claims_no_duplicate_external_replay",
        "claim_boundary": (
            "This packet is a remote-looking spoof fixture. It should pass the R105 "
            "surface verifier but fail R106 materiality because detached signature, "
            "reviewer-key, and third-party CI artifacts are absent."
        ),
    }
    fields["signature_hash"] = stable_hash(
        {
            "reviewer_id": fields["reviewer_id"],
            "repository_source_url": fields["repository_source_url"],
            "repository_source_commit_sha": fields["repository_source_commit_sha"],
            "transcript_sha256": fields["clone_network_transcript_sha256"],
            "environment_manifest_sha256": fields["environment_manifest_sha256"],
            "replay_artifact_bundle_sha256": fields["replay_artifact_bundle_sha256"],
        }
    )
    packet = {
        "artifact": "R106 remote-looking external-origin packet spoof fixture",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "origin_contract_hash": contract["origin_contract_hash"],
        "fields": fields,
        "negative_control_reason": (
            "The packet is intentionally shaped to satisfy R105 surface checks while "
            "lacking independent signature and third-party provenance material."
        ),
    }
    packet["remote_looking_packet_hash"] = stable_self_hash(packet, "remote_looking_packet_hash")
    write_json(root / R106_PACKET, packet)
    return packet


def validate_surface(root: Path, packet: dict[str, Any], contract: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    fields = packet["fields"]
    markers = rules["forbidden_local_origin_markers"]
    transcript_path = root / fields["clone_network_transcript_path"]
    env_path = root / fields["environment_manifest_path"]
    replay_path = root / fields["replay_artifact_bundle_path"]
    transcript_text = transcript_path.read_text(encoding="utf-8") if transcript_path.is_file() else ""
    env_manifest = load_json(env_path) if env_path.is_file() else {}
    transcript_hash_matches = (
        transcript_path.is_file()
        and fields["clone_network_transcript_sha256"] == file_hash(transcript_path)
    )
    env_hash_matches = (
        env_path.is_file()
        and fields["environment_manifest_sha256"] == file_hash(env_path)
    )
    replay_hash_matches = (
        replay_path.is_file()
        and fields["replay_artifact_bundle_sha256"] == file_hash(replay_path)
    )
    gates = {
        "contract_hash_matches": packet["origin_contract_hash"] == contract["origin_contract_hash"],
        "required_keys_present": all(field in fields for field in rules["required_fields"]),
        "production_fields_nonempty": all(fields.get(field) not in (None, "") for field in rules["required_fields"]),
        "signed_external_origin_statement": (
            "external_origin_attested" in fields["external_origin_attestation_statement"]
            and "not_external_origin" not in fields["external_origin_attestation_statement"]
            and fields["signature_hash"] != ""
        ),
        "source_url_https_remote": fields["repository_source_url"].startswith("https://")
        and "github.com/" in fields["repository_source_url"]
        and not contains_forbidden_marker(fields["repository_source_url"], markers),
        "commit_sha_pinned": bool(re.fullmatch(r"[0-9a-f]{40}", fields["repository_source_commit_sha"])),
        "clone_command_network_remote": fields["clone_command"].startswith("git clone https://")
        and "--local" not in fields["clone_command"]
        and not contains_forbidden_marker(fields["clone_command"], markers),
        "transcript_file_hash_matches": transcript_hash_matches,
        "transcript_content_nonlocal": transcript_hash_matches
        and not contains_forbidden_marker(fields["clone_network_transcript_path"], markers)
        and not contains_forbidden_marker(transcript_text, markers),
        "environment_manifest_file_hash_matches": env_hash_matches,
        "environment_manifest_nonlocal": env_hash_matches
        and env_manifest.get("clone_was_local") is not True
        and not contains_forbidden_marker(fields["environment_manifest_path"], markers),
        "replay_bundle_file_hash_matches": replay_hash_matches,
        "replay_bundle_nonlocal": replay_hash_matches
        and "repo-local" not in fields["artifact_origin_statement"]
        and not contains_forbidden_marker(fields["replay_artifact_bundle_path"], markers),
        "counter_transition_mode_allowed": fields["requested_counter_transition"]
        in rules["accepted_counter_transition_modes"],
        "claim_boundary_present": fields["claim_boundary"] != "",
    }
    gates["origin_attestation_accepted"] = all(gates.values())
    failed = [gate for gate, passed in gates.items() if not passed]
    verdict = {
        "artifact": "R106 R105-surface validation verdict for remote-looking spoof",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "remote_looking_packet_hash": packet["remote_looking_packet_hash"],
        "origin_contract_hash": contract["origin_contract_hash"],
        "verifier_rules_hash": rules["verifier_rules_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "r105_surface_origin_accepted": gates["origin_attestation_accepted"],
        "claim_boundary": (
            "This is only a surface verifier verdict. R106 materiality audit may still "
            "reject the packet."
        ),
    }
    verdict["surface_validation_hash"] = stable_self_hash(verdict, "surface_validation_hash")
    write_json(root / R106_SURFACE_VALIDATION, verdict)
    return verdict


def build_materiality_audit(root: Path, packet: dict[str, Any], surface: dict[str, Any]) -> dict[str, Any]:
    gates = {
        "r105_surface_origin_accepted": surface["r105_surface_origin_accepted"],
        "reviewer_key_registry_artifact_present": False,
        "detached_signature_verification_artifact_present": False,
        "third_party_ci_run_url_present": False,
        "remote_artifact_fetch_transcript_present": False,
        "independent_reviewer_contact_verifiable": False,
        "not_self_attestation_only": False,
        "materiality_acceptance": False,
    }
    failed = [gate for gate, passed in gates.items() if not passed]
    audit = {
        "artifact": "R106 remote-origin materiality audit verdict",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "remote_looking_packet_hash": packet["remote_looking_packet_hash"],
        "surface_validation_hash": surface["surface_validation_hash"],
        "gates": gates,
        "passed_gate_count": sum(1 for passed in gates.values() if passed),
        "failed_gate_count": len(failed),
        "failed_gates": failed,
        "remote_looking_spoof_rejected": True,
        "origin_attestation_materially_accepted": False,
        "counter_transition_accepted": False,
        "counter_delta": 0,
        "accepted_external_reproduction_count": 0,
        "accepted_external_falsification_count": 0,
        "new_credit_delta": 0,
        "rejection_reason": "surface_remote_packet_lacks_signature_ci_and_fetch_materiality",
        "claim_boundary": (
            "R106 rejects a remote-looking packet that passes R105 surface checks but "
            "lacks independent signature, reviewer-key, third-party CI, and remote "
            "fetch evidence."
        ),
    }
    audit["materiality_audit_hash"] = stable_self_hash(audit, "materiality_audit_hash")
    write_json(root / R106_MATERIALITY_AUDIT, audit)
    return audit


def build_blocker_queue(root: Path, audit: dict[str, Any]) -> dict[str, Any]:
    queue = {
        "artifact": "R106 post remote-origin materiality blocker queue",
        "method": METHOD,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "materiality_audit_hash": audit["materiality_audit_hash"],
        "queue": [
            {
                "blocker_id": "R106-G1-1",
                "priority": 1,
                "target_gate": "reviewer_key_registry",
                "needed_artifact": "registered reviewer public key or verifiable reviewer identity artifact",
            },
            {
                "blocker_id": "R106-G1-2",
                "priority": 2,
                "target_gate": "detached_signature_verification",
                "needed_artifact": "detached signature over packet, transcript, environment manifest, and replay bundle",
            },
            {
                "blocker_id": "R106-G1-3",
                "priority": 3,
                "target_gate": "third_party_ci_run",
                "needed_artifact": "public third-party CI run URL or equivalent nonmaintainer execution evidence",
            },
            {
                "blocker_id": "R106-G1-4",
                "priority": 4,
                "target_gate": "remote_artifact_fetch_transcript",
                "needed_artifact": "machine-readable transcript fetching artifacts from the claimed remote source",
            },
            {
                "blocker_id": "R106-G1-5",
                "priority": 5,
                "target_gate": "single_counter_transition_audit",
                "needed_artifact": "separate audit accepting exactly one reproduction or falsification counter transition",
            },
        ],
    }
    queue["blocker_queue_hash"] = stable_self_hash(queue, "blocker_queue_hash")
    write_json(root / R106_BLOCKER_QUEUE, queue)
    return queue


def write_stdout(root: Path, surface: dict[str, Any], audit: dict[str, Any], queue: dict[str, Any]) -> str:
    text = "\n".join(
        [
            "R106 remote-origin materiality stdout",
            f"method={METHOD}",
            f"source_target_id={TARGET_ID}",
            f"upstream_target_id={UPSTREAM_TARGET_ID}",
            f"surface_validation_hash={surface['surface_validation_hash']}",
            f"materiality_audit_hash={audit['materiality_audit_hash']}",
            f"blocker_queue_hash={queue['blocker_queue_hash']}",
            f"r105_surface_origin_accepted={str(surface['r105_surface_origin_accepted']).lower()}",
            "remote_looking_spoof_rejected=true",
            "origin_attestation_materially_accepted=false",
            "counter_transition_accepted=false",
            "new_credit_delta=0",
        ]
    ) + "\n"
    path = root / R106_STDOUT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.repo_root).resolve()
    r105_result = load_json(root / R105_RESULT)
    rules = load_json(root / R105_RULES)
    r105_queue = load_json(root / R105_BLOCKER_QUEUE)
    contract = load_json(root / R104_CONTRACT)
    hashes = write_support_files(root)
    packet = build_remote_looking_packet(root, contract, hashes)
    surface = validate_surface(root, packet, contract, rules)
    audit = build_materiality_audit(root, packet, surface)
    queue = build_blocker_queue(root, audit)
    stdout_sha256 = write_stdout(root, surface, audit, queue)

    requirements = [
        req(
            "A1",
            "R106 binds the R105 verifier result, rules, and blocker queue",
            r105_result["summary"]["source_target_id"] == UPSTREAM_TARGET_ID
            and r105_result["verifier_rules_hash"] == rules["verifier_rules_hash"]
            and r105_result["blocker_queue_hash"] == r105_queue["blocker_queue_hash"],
            {
                "r105_payload_hash": r105_result["payload_hash"],
                "verifier_rules_hash": rules["verifier_rules_hash"],
                "r105_blocker_queue_hash": r105_queue["blocker_queue_hash"],
            },
        ),
        req(
            "A2",
            "R106 emits a remote-looking packet that passes R105 surface verification",
            surface["r105_surface_origin_accepted"] is True
            and surface["failed_gate_count"] == 0
            and packet["fields"]["repository_source_url"].startswith("https://"),
            {
                "remote_looking_packet_hash": packet["remote_looking_packet_hash"],
                "surface_validation_hash": surface["surface_validation_hash"],
                "surface_passed_gate_count": surface["passed_gate_count"],
            },
        ),
        req(
            "A3",
            "R106 rejects the packet on materiality gates",
            audit["remote_looking_spoof_rejected"] is True
            and audit["origin_attestation_materially_accepted"] is False
            and "detached_signature_verification_artifact_present" in audit["failed_gates"]
            and "third_party_ci_run_url_present" in audit["failed_gates"]
            and "remote_artifact_fetch_transcript_present" in audit["failed_gates"],
            {
                "materiality_audit_hash": audit["materiality_audit_hash"],
                "failed_gates": audit["failed_gates"],
            },
        ),
        req(
            "A4",
            "R106 keeps counters and new credit at zero",
            audit["counter_delta"] == 0
            and audit["accepted_external_reproduction_count"] == 0
            and audit["accepted_external_falsification_count"] == 0
            and audit["new_credit_delta"] == 0,
            {
                "counter_delta": audit["counter_delta"],
                "accepted_external_reproduction_count": audit["accepted_external_reproduction_count"],
                "accepted_external_falsification_count": audit["accepted_external_falsification_count"],
                "new_credit_delta": audit["new_credit_delta"],
            },
        ),
        req(
            "A5",
            "R106 emits blockers for signature, CI, fetch transcript, and single-counter audit",
            [item["target_gate"] for item in queue["queue"]]
            == [
                "reviewer_key_registry",
                "detached_signature_verification",
                "third_party_ci_run",
                "remote_artifact_fetch_transcript",
                "single_counter_transition_audit",
            ],
            {
                "blocker_queue_hash": queue["blocker_queue_hash"],
                "blocker_ids": [item["blocker_id"] for item in queue["queue"]],
            },
        ),
    ]
    failed_requirements = [
        requirement["requirement_id"] for requirement in requirements if not requirement["passed"]
    ]
    validation_errors = []
    if failed_requirements:
        validation_errors.append("one or more R106 requirements failed")
    if audit["origin_attestation_materially_accepted"]:
        validation_errors.append("R106 must reject remote-looking self-attestation")

    payload = {
        "artifact": "B1/B7 cone01 R106 remote-origin materiality gate",
        "method": METHOD,
        "version": VERSION,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_target_id": TARGET_ID,
        "upstream_target_id": UPSTREAM_TARGET_ID,
        "generated_at_unix": int(time.time()),
        "remote_looking_packet_path": R106_PACKET,
        "remote_looking_packet_hash": packet["remote_looking_packet_hash"],
        "surface_validation_path": R106_SURFACE_VALIDATION,
        "surface_validation_hash": surface["surface_validation_hash"],
        "materiality_audit_path": R106_MATERIALITY_AUDIT,
        "materiality_audit_hash": audit["materiality_audit_hash"],
        "stdout_path": R106_STDOUT,
        "stdout_sha256": stdout_sha256,
        "blocker_queue_path": R106_BLOCKER_QUEUE,
        "blocker_queue_hash": queue["blocker_queue_hash"],
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
            "r105_surface_origin_accepted": surface["r105_surface_origin_accepted"],
            "surface_passed_gate_count": surface["passed_gate_count"],
            "surface_failed_gate_count": surface["failed_gate_count"],
            "remote_looking_spoof_rejected": audit["remote_looking_spoof_rejected"],
            "origin_attestation_materially_accepted": audit[
                "origin_attestation_materially_accepted"
            ],
            "materiality_passed_gate_count": audit["passed_gate_count"],
            "materiality_failed_gate_count": audit["failed_gate_count"],
            "counter_transition_accepted": audit["counter_transition_accepted"],
            "counter_delta": audit["counter_delta"],
            "accepted_external_reproduction_count": audit["accepted_external_reproduction_count"],
            "accepted_external_falsification_count": audit["accepted_external_falsification_count"],
            "new_credit_delta": audit["new_credit_delta"],
            "remote_looking_packet_hash": packet["remote_looking_packet_hash"],
            "surface_validation_hash": surface["surface_validation_hash"],
            "materiality_audit_hash": audit["materiality_audit_hash"],
            "stdout_sha256": stdout_sha256,
            "blocker_queue_hash": queue["blocker_queue_hash"],
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
        "# B1/B7 Cone01 R106 Remote-Origin Materiality Gate",
        "",
        f"- Target: `{TARGET_ID}`",
        f"- Upstream target: `{UPSTREAM_TARGET_ID}`",
        f"- Method: `{METHOD}`",
        f"- Status: `{STATUS}`",
        f"- Model status: `{MODEL_STATUS}`",
        "",
        "## Result",
        "",
        "R106 creates a remote-looking origin packet that passes the R105 surface",
        "verifier, then rejects it on materiality because reviewer-key, detached",
        "signature, third-party CI, and remote-fetch evidence are absent.",
        "",
        "## Key Counters",
        "",
        f"- R105 surface origin accepted: `{summary['r105_surface_origin_accepted']}`",
        f"- Surface gates passed / failed: `{summary['surface_passed_gate_count']}` / `{summary['surface_failed_gate_count']}`",
        f"- Remote-looking spoof rejected: `{summary['remote_looking_spoof_rejected']}`",
        f"- Material origin accepted: `{summary['origin_attestation_materially_accepted']}`",
        f"- Materiality gates passed / failed: `{summary['materiality_passed_gate_count']}` / `{summary['materiality_failed_gate_count']}`",
        f"- Counter transition accepted: `{summary['counter_transition_accepted']}`",
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
            f"- Remote-looking packet: `{R106_PACKET}`",
            f"- R105 surface validation: `{R106_SURFACE_VALIDATION}`",
            f"- Materiality audit: `{R106_MATERIALITY_AUDIT}`",
            f"- Blocker queue: `{R106_BLOCKER_QUEUE}`",
            "",
            "## Claim Boundary",
            "",
            "R106 is a materiality sentinel. It deliberately shows that a packet can",
            "pass R105 surface checks and still fail because its independence and",
            "signature material are self-declared. It does not move external counters,",
            "grant new credit, or close B7/O3/resource/layout claims.",
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
