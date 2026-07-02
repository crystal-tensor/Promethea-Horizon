#!/usr/bin/env python3
"""T-B4-002j/T-B8-003n: priority real-backend transcript packet gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b4_b8_real_backend_transcript_priority_packet_gate_v0"
STATUS = "real_backend_transcript_priority_packet_open_missing_artifact"
MODEL_STATUS = "priority_real_backend_transcript_packet_ready_no_rows_submitted"
VERSION = "0.1"
EXPECTED_PACKET_ID = "B4B8-M6-real-backend-transcript-rows"
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
    intake = load_json(args.intake_template)
    summary = intake["summary"]
    packet = next(
        (row for row in intake["intake_packets"] if row["packet_id"] == EXPECTED_PACKET_ID),
        None,
    )
    submission_path = args.submission_dir / f"{EXPECTED_PACKET_ID}.json"
    required_row_keys = list(intake["required_row_keys"])
    production_required_keys = list(intake["production_required_keys"])
    submitted_exists = submission_path.exists()
    submitted = load_json(submission_path) if submitted_exists else None
    submitted_keys = sorted(submitted) if submitted else []
    missing_keys = [key for key in required_row_keys if submitted is None or key not in submitted]
    production_present = [
        key for key in production_required_keys if submitted is not None and submitted.get(key) is not None
    ]
    source_backed = (
        submitted is not None
        and submitted.get("source_evidence_files_present") is True
        and len(production_present) == len(production_required_keys)
    )
    budget_accountable = (
        submitted is not None
        and submitted.get("total_count") == summary["holdout_row_count"]
        and submitted.get("accepted_count") is not None
        and submitted.get("acceptance_rate") is not None
    )

    priority_packet = {
        "packet_id": EXPECTED_PACKET_ID,
        "blocks_margin_gate": packet["blocks_margin_gate"] if packet else None,
        "owner_role": packet["owner_role"] if packet else None,
        "template_hash": packet["template_hash"] if packet else None,
        "submission_artifact_path": str(submission_path),
        "required_row_keys": required_row_keys,
        "production_required_keys": production_required_keys,
        "required_evidence_files": [
            "backend_properties_manifest",
            "hashed_backend_job_metadata",
            "executed_openqasm3_or_transpiled_circuit_manifest",
            "hidden_predicate_mask_commitment",
            "raw_counts_artifact",
            "readout_mitigation_or_no_mitigation_manifest",
            "postprocess_script",
            "calibration_timestamp_source",
        ],
        "accepted_only_if": [
            "all 19 transcript row keys are present",
            "all 10 production-required keys are non-null and source-backed",
            "total_count equals the locked 160-row holdout denominator or declares a reviewed replacement denominator",
            "accepted_count and acceptance_rate replay from raw_counts_sha256 and postprocess_script_sha256",
            "the row declares leakage_condition and private_predicate_bit_count before scoring",
            "claim_boundary forbids protocol soundness, quantum advantage, sampling hardness, and BQP separation claims",
        ],
        "margin_retest_budgets": {
            "leakage_blind_no_leak_allowed_accepts_per_160": summary["no_leak_allowed_accepts_per_160"],
            "full_private_material_leak_allowed_accepts_per_160": summary[
                "full_leak_allowed_accepts_per_160"
            ],
        },
    }
    priority_packet["packet_hash"] = stable_hash(priority_packet)

    forbidden_claims = [
        "protocol_soundness_proved",
        "cryptographic_soundness_proved",
        "sampling_hardness_proved",
        "quantum_advantage_claimed",
        "bqp_separation_claimed",
    ]
    requirements = [
        requirement(
            "P1",
            "Intake template remains valid and open on real-backend transcript rows",
            intake.get("method") == "b4_b8_real_backend_transcript_intake_template_gate_v0"
            and summary.get("validation_error_count") == 0
            and summary.get("failed_intake_requirement_ids") == ["T5", "T6", "T7"],
            {
                "source_status": intake.get("status"),
                "failed_intake_requirement_ids": summary.get("failed_intake_requirement_ids"),
                "validation_error_count": summary.get("validation_error_count"),
            },
        ),
        requirement(
            "P2",
            "Priority packet is fixed to the first real-backend transcript row blocker",
            packet is not None
            and packet["packet_id"] == EXPECTED_PACKET_ID
            and packet["blocks_margin_gate"] == "M6",
            {
                "expected_packet_id": EXPECTED_PACKET_ID,
                "actual_packet_id": packet["packet_id"] if packet else None,
                "blocks_margin_gate": packet["blocks_margin_gate"] if packet else None,
            },
        ),
        requirement(
            "P3",
            "Transcript packet carries the 19-key schema and 10 production keys",
            len(required_row_keys) == 19 and len(production_required_keys) == 10,
            {
                "required_row_key_count": len(required_row_keys),
                "production_required_key_count": len(production_required_keys),
            },
        ),
        requirement(
            "P4",
            "Packet binds required backend evidence file classes",
            len(priority_packet["required_evidence_files"]) == 8,
            {"required_evidence_files": priority_packet["required_evidence_files"]},
        ),
        requirement(
            "P5",
            "Locked margin budgets are preserved for later retest",
            summary.get("holdout_row_count") == 160
            and summary.get("no_leak_allowed_accepts_per_160") == 16
            and summary.get("full_leak_allowed_accepts_per_160") == 40,
            {
                "holdout_row_count": summary.get("holdout_row_count"),
                "no_leak_allowed_accepts_per_160": summary.get(
                    "no_leak_allowed_accepts_per_160"
                ),
                "full_leak_allowed_accepts_per_160": summary.get(
                    "full_leak_allowed_accepts_per_160"
                ),
            },
        ),
        requirement(
            "P6",
            "Priority real-backend transcript artifact has been submitted",
            submitted_exists,
            {"submission_artifact_path": str(submission_path), "exists": submitted_exists},
        ),
        requirement(
            "P7",
            "Submitted artifact satisfies the locked 19-key transcript schema",
            submitted_exists and not missing_keys,
            {"submitted_key_count": len(submitted_keys), "missing_keys": missing_keys},
        ),
        requirement(
            "P8",
            "Submitted production keys are source-backed and budget-accountable",
            source_backed and budget_accountable,
            {
                "production_keys_present": production_present,
                "production_required_keys": production_required_keys,
                "source_evidence_files_present": submitted.get("source_evidence_files_present")
                if submitted
                else False,
                "budget_accountable": budget_accountable,
            },
        ),
        requirement(
            "P9",
            "Forbidden soundness, advantage, and BQP claims remain false",
            all(summary.get(key) is False for key in forbidden_claims),
            {key: summary.get(key) for key in forbidden_claims},
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected priority transcript packet failures: {failed_ids}")
    if submitted_exists:
        validation_errors.append("gate expected no submitted artifact until a hardware PR supplies one")

    payload_summary = {
        "priority_packet_id": EXPECTED_PACKET_ID,
        "packet_hash": priority_packet["packet_hash"],
        "priority_requirement_count": len(requirements),
        "priority_requirements_passed": passed,
        "priority_requirements_failed": len(requirements) - passed,
        "failed_priority_requirement_ids": failed_ids,
        "required_row_key_count": len(required_row_keys),
        "production_required_key_count": len(production_required_keys),
        "required_evidence_file_count": len(priority_packet["required_evidence_files"]),
        "holdout_row_count": summary.get("holdout_row_count"),
        "real_backend_transcript_rows": summary.get("real_backend_transcript_rows"),
        "submitted_artifact_exists": submitted_exists,
        "submitted_key_count": len(submitted_keys),
        "missing_key_count": len(missing_keys),
        "production_keys_present_count": len(production_present),
        "accepted_priority_transcript_rows": 0,
        "no_leak_allowed_accepts_per_160": summary.get("no_leak_allowed_accepts_per_160"),
        "full_leak_allowed_accepts_per_160": summary.get("full_leak_allowed_accepts_per_160"),
        "protocol_soundness_proved": False,
        "cryptographic_soundness_proved": False,
        "sampling_hardness_proved": False,
        "quantum_advantage_claimed": False,
        "bqp_separation_claimed": False,
        "validation_error_count": len(validation_errors),
    }

    return {
        "benchmark": "B4/B8",
        "benchmark_id": "B4_B8",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T2",
        "dependency_benchmarks": ["B4", "B8", "B10"],
        "title": "B4/B8 Real-Backend Transcript Priority Packet Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_intake_template_result": str(args.intake_template),
        "summary": payload_summary,
        "priority_transcript_packet": priority_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The first B4/B8 real-backend evidence blocker now has a concrete "
                "source-backed transcript submission packet for the M6 row requirement."
            ),
            "what_is_not_supported": (
                "No real-backend transcript row has been submitted or accepted; the margin "
                "gate is not ready to rerun and no protocol soundness, quantum advantage, "
                "sampling-hardness, cryptographic-soundness, or BQP-separation claim is supported."
            ),
            "next_gate": (
                f"Submit {submission_path} with all 19 transcript keys, all 10 source-backed "
                "production keys, raw-count and postprocess hashes, and replayable accepted_count "
                "against the locked 160-row margin denominator."
            ),
            "protocol_soundness_proved": False,
            "cryptographic_soundness_proved": False,
            "sampling_hardness_proved": False,
            "quantum_advantage_claimed": False,
            "bqp_separation_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": time.time() - started,
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    packet = payload["priority_transcript_packet"]
    lines = [
        "# B4/B8 Real-Backend Transcript Priority Packet Gate",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Model status: `{payload['model_status']}`",
        f"- Priority packet: `{summary['priority_packet_id']}`",
        f"- Packet hash: `{summary['packet_hash']}`",
        f"- Requirements passed/failed: {summary['priority_requirements_passed']} / {summary['priority_requirements_failed']}",
        f"- Failed requirement IDs: {summary['failed_priority_requirement_ids']}",
        f"- Transcript row schema keys: {summary['required_row_key_count']}",
        f"- Production-required row keys: {summary['production_required_key_count']}",
        f"- Required evidence file classes: {summary['required_evidence_file_count']}",
        f"- Holdout rows / real backend rows: {summary['holdout_row_count']} / {summary['real_backend_transcript_rows']}",
        f"- No-leak budget: <= {summary['no_leak_allowed_accepts_per_160']} accepts per 160",
        f"- Full-leak budget: <= {summary['full_leak_allowed_accepts_per_160']} accepts per 160",
        f"- Submitted artifact exists: {summary['submitted_artifact_exists']}",
        f"- Accepted priority transcript rows: {summary['accepted_priority_transcript_rows']}",
        "",
        "## Submission Packet",
        "",
        f"- Submission path: `{packet['submission_artifact_path']}`",
        f"- Blocks margin gate: `{packet['blocks_margin_gate']}`",
        f"- Owner role: `{packet['owner_role']}`",
        "",
        "Required evidence files:",
        "",
    ]
    for item in packet["required_evidence_files"]:
        lines.append(f"- {item}")
    lines.extend(["", "Acceptance predicates:", ""])
    for item in packet["accepted_only_if"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Transcript Row Schema",
            "",
            ", ".join(packet["required_row_keys"]),
            "",
            "## Requirement Results",
            "",
        ]
    )
    for row in payload["requirements"]:
        status = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{status}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- protocol_soundness_proved: {payload['claim_boundary']['protocol_soundness_proved']}",
            f"- quantum_advantage_claimed: {payload['claim_boundary']['quantum_advantage_claimed']}",
            f"- bqp_separation_claimed: {payload['claim_boundary']['bqp_separation_claimed']}",
            "",
            "## Validation",
            "",
            f"- validation_error_count: {summary['validation_error_count']}",
        ]
    )
    if payload["validation_errors"]:
        for error in payload["validation_errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--intake-template",
        type=Path,
        default=Path("results/B4_B8_real_backend_transcript_intake_template_gate_v0.json"),
    )
    parser.add_argument(
        "--submission-dir",
        type=Path,
        default=Path("results/B4_B8_real_backend_transcript_priority_submissions"),
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B4_B8_real_backend_transcript_priority_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B4_B8_real_backend_transcript_priority_packet_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-02")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, pretty=args.pretty)
    write_markdown(payload, args.markdown_output)

    print(json.dumps(payload["summary"], indent=2 if args.pretty else None, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
