#!/usr/bin/env python3
"""T-B5-006n/T-B10-014l: priority W1 row submission-packet gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b5_b10_w1_priority_row_submission_packet_gate_v0"
STATUS = "w1_priority_row_submission_packet_open_missing_artifact"
MODEL_STATUS = "priority_row_contract_packet_ready_no_production_row_submitted"
VERSION = "0.1"
EXPECTED_ROW_CONTRACT_HASH = "7ee407e20f51bd0c003d885c8d43282359f84bea9729f0da203b9b2c2970a9fc"
EXPECTED_PRIORITY_ROW_ID = "D5H_s8_u2_eta0.25_n4x4_obs_density_site_4"
EXPECTED_FAILED_IDS = ["P6", "P7", "P8"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def stable_hash(payload: Any) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def requirement(requirement_id: str, label: str, passed: bool, evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": requirement_id,
        "label": label,
        "passed": bool(passed),
        "evidence": evidence,
    }


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    started = time.time()
    queue = load_json(args.blocker_queue)
    implementation = load_json(args.implementation_contract)

    row_queue = queue.get("row_queue", [])
    priority_row = next((row for row in row_queue if int(row["priority"]) == 1), None)
    row_schema = implementation["row_artifact_schema"]
    required_row_keys = list(row_schema["required_row_keys"])
    production_required_keys = list(queue.get("production_required_keys", []))
    submission_dir = args.submission_dir
    submission_artifact_path = submission_dir / f"{EXPECTED_PRIORITY_ROW_ID}.json"

    if priority_row is None:
        packet: dict[str, Any] = {}
    else:
        packet = {
            "row_id": priority_row["row_id"],
            "priority": priority_row["priority"],
            "sites": priority_row["sites"],
            "u_over_t": priority_row["u_over_t"],
            "row_contract_hash": queue["summary"]["row_contract_hash"],
            "template_hash": priority_row["template_hash"],
            "prototype_trace_hash": priority_row["prototype_trace_hash"],
            "prototype_values_are_provenance_only": True,
            "required_row_keys": required_row_keys,
            "production_required_keys": production_required_keys,
            "blocking_packet_ids": priority_row["blocking_packet_ids"],
            "required_evidence_files": [
                "canonical_mps_or_dmrg_state_manifest",
                "left_environment_hash_source",
                "right_environment_hash_source",
                "orthonormal_residual_norm_calculation",
                "discarded_weight_or_truncation_log",
                "wall_clock_and_peak_memory_log",
                "sweep_or_matvec_count_log",
                "same_access_replay_command",
            ],
            "submission_artifact_path": str(submission_artifact_path),
            "accepted_only_if": [
                "all 17 required row keys are present",
                "all 8 production-required keys are non-null and source-backed",
                "row_contract_hash equals the locked B5/B10 W1 hash",
                "canonical environment hashes are derived from submitted state/environment artifacts",
                "orthonormal residual and discarded weight are numeric and threshold-declared",
                "wall-clock, memory, and sweep/matvec counts are measured under same-access conditions",
                "no prototype value is promoted into production evidence",
            ],
        }
    packet_hash = stable_hash(packet) if packet else None
    submitted_artifact_exists = submission_artifact_path.exists()
    submitted_artifact: dict[str, Any] | None = None
    if submitted_artifact_exists:
        submitted_artifact = load_json(submission_artifact_path)

    submitted_required_keys = sorted(submitted_artifact) if submitted_artifact else []
    missing_submitted_keys = [
        key for key in required_row_keys if submitted_artifact is None or key not in submitted_artifact
    ]
    production_keys_present = [
        key
        for key in production_required_keys
        if submitted_artifact is not None and submitted_artifact.get(key) is not None
    ]
    production_keys_source_backed = (
        submitted_artifact is not None
        and submitted_artifact.get("source_evidence_files_present") is True
        and len(production_keys_present) == len(production_required_keys)
    )

    requirements = [
        requirement(
            "P1",
            "Blocker queue preserves the locked W1 row contract",
            queue.get("method") == "b5_b10_w1_production_row_blocker_queue_gate_v0"
            and queue["summary"].get("row_contract_hash") == EXPECTED_ROW_CONTRACT_HASH
            and queue["summary"].get("validation_error_count") == 0,
            {
                "source_status": queue.get("status"),
                "row_contract_hash": queue["summary"].get("row_contract_hash"),
                "validation_error_count": queue["summary"].get("validation_error_count"),
            },
        ),
        requirement(
            "P2",
            "Priority row is fixed and matches the queue head",
            priority_row is not None and priority_row["row_id"] == EXPECTED_PRIORITY_ROW_ID,
            {
                "expected_priority_row_id": EXPECTED_PRIORITY_ROW_ID,
                "actual_priority_row_id": priority_row["row_id"] if priority_row else None,
            },
        ),
        requirement(
            "P3",
            "Submission packet carries the full 17-key row schema and 8 production keys",
            len(required_row_keys) == 17
            and len(production_required_keys) == 8
            and sorted(production_required_keys) == sorted(priority_row["missing_production_fields"]),
            {
                "required_row_key_count": len(required_row_keys),
                "production_required_key_count": len(production_required_keys),
                "priority_missing_fields": priority_row["missing_production_fields"] if priority_row else None,
            },
        ),
        requirement(
            "P4",
            "Packet binds every required evidence file class before acceptance",
            len(packet.get("required_evidence_files", [])) == 8,
            {"required_evidence_files": packet.get("required_evidence_files", [])},
        ),
        requirement(
            "P5",
            "Prototype values are explicitly provenance-only",
            packet.get("prototype_values_are_provenance_only") is True,
            {
                "prototype_trace_hash": packet.get("prototype_trace_hash"),
                "prototype_values_are_provenance_only": packet.get(
                    "prototype_values_are_provenance_only"
                ),
            },
        ),
        requirement(
            "P6",
            "Priority-row production artifact has been submitted",
            submitted_artifact_exists,
            {"submission_artifact_path": str(submission_artifact_path), "exists": submitted_artifact_exists},
        ),
        requirement(
            "P7",
            "Submitted artifact satisfies the locked 17-key schema",
            submitted_artifact_exists and not missing_submitted_keys,
            {"submitted_key_count": len(submitted_required_keys), "missing_submitted_keys": missing_submitted_keys},
        ),
        requirement(
            "P8",
            "Submitted production keys are source-backed and non-null",
            production_keys_source_backed,
            {
                "production_keys_present": production_keys_present,
                "production_required_keys": production_required_keys,
                "source_evidence_files_present": submitted_artifact.get("source_evidence_files_present")
                if submitted_artifact
                else False,
            },
        ),
        requirement(
            "P9",
            "Forbidden positive-route claims remain false",
            all(
                queue["summary"].get(key) is False
                for key in [
                    "production_dmrg_claimed",
                    "same_access_positive_route_claimed",
                    "quantum_advantage_claimed",
                    "bqp_separation_claimed",
                ]
            ),
            {
                "production_dmrg_claimed": queue["summary"].get("production_dmrg_claimed"),
                "same_access_positive_route_claimed": queue["summary"].get(
                    "same_access_positive_route_claimed"
                ),
                "quantum_advantage_claimed": queue["summary"].get("quantum_advantage_claimed"),
                "bqp_separation_claimed": queue["summary"].get("bqp_separation_claimed"),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected priority-row packet failures: {failed_ids}")
    if submitted_artifact_exists:
        validation_errors.append("gate expected no submitted artifact until a solver PR supplies one")

    summary = {
        "row_contract_hash": queue["summary"].get("row_contract_hash"),
        "priority_row_id": priority_row["row_id"] if priority_row else None,
        "packet_hash": packet_hash,
        "packet_requirement_count": len(requirements),
        "packet_requirements_passed": passed,
        "packet_requirements_failed": len(requirements) - passed,
        "failed_packet_requirement_ids": failed_ids,
        "required_row_key_count": len(required_row_keys),
        "production_required_key_count": len(production_required_keys),
        "required_evidence_file_count": len(packet.get("required_evidence_files", [])),
        "submitted_artifact_exists": submitted_artifact_exists,
        "submitted_key_count": len(submitted_required_keys),
        "missing_submitted_key_count": len(missing_submitted_keys),
        "production_keys_present_count": len(production_keys_present),
        "accepted_priority_row_count": 0,
        "production_dmrg_claimed": False,
        "same_access_positive_route_claimed": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark_id": "B5",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T1",
        "dependency_benchmarks": ["B5", "B10"],
        "title": "B5/B10 W1 Priority Row Submission Packet Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_blocker_queue_result": str(args.blocker_queue),
        "source_implementation_contract_result": str(args.implementation_contract),
        "summary": summary,
        "priority_row_submission_packet": packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The priority W1 row now has a concrete submission packet and acceptance "
                "contract binding all 17 row keys, all 8 production-required keys, and "
                "the evidence files needed for environment, convergence, and cost review."
            ),
            "what_is_not_supported": (
                "No priority-row artifact has been submitted or accepted; no production DMRG "
                "denominator, same-access positive route, quantum advantage, or BQP separation "
                "is supported."
            ),
            "next_gate": (
                f"Submit {submission_artifact_path} with source-backed production keys and "
                "same-access cost logs, then rerun this gate before any row acceptance."
            ),
            "production_dmrg_claimed": False,
            "same_access_positive_route_claimed": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    packet = payload["priority_row_submission_packet"]
    lines = [
        "# B5/B10 W1 Priority Row Submission Packet Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Priority row: `{summary['priority_row_id']}`",
        f"- Packet hash: `{summary['packet_hash']}`",
        f"- Requirements passed/failed: {summary['packet_requirements_passed']} / {summary['packet_requirements_failed']}",
        f"- Failed requirement IDs: {summary['failed_packet_requirement_ids']}",
        f"- Required row keys / production keys: {summary['required_row_key_count']} / {summary['production_required_key_count']}",
        f"- Required evidence files: {summary['required_evidence_file_count']}",
        f"- Submitted artifact exists: {summary['submitted_artifact_exists']}",
        "",
        "## Priority Row Packet",
        "",
        f"- row_id: `{packet.get('row_id')}`",
        f"- submission_artifact_path: `{packet.get('submission_artifact_path')}`",
        f"- template_hash: `{packet.get('template_hash')}`",
        f"- prototype_trace_hash: `{packet.get('prototype_trace_hash')}`",
        f"- blocking packets: {packet.get('blocking_packet_ids')}",
        "",
        "## Required Evidence Files",
        "",
    ]
    for item in packet.get("required_evidence_files", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Acceptance Conditions", ""])
    for item in packet.get("accepted_only_if", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Requirement Results", ""])
    for item in payload["requirements"]:
        state = "PASS" if item["passed"] else "FAIL"
        lines.append(f"- {item['requirement_id']} [{state}]: {item['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- production_dmrg_claimed: {payload['claim_boundary']['production_dmrg_claimed']}",
            f"- same_access_positive_route_claimed: {payload['claim_boundary']['same_access_positive_route_claimed']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {summary['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        lines.extend(f"- {error}" for error in payload["validation_errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--blocker-queue",
        type=Path,
        default=Path("results/B5_B10_w1_production_row_blocker_queue_gate_v0.json"),
    )
    parser.add_argument(
        "--implementation-contract",
        type=Path,
        default=Path("results/B5_B10_w1_implementation_contract_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B5_B10_w1_priority_row_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B5_B10_w1_priority_row_submission_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B5_B10_w1_priority_row_submission_packet_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-02")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
