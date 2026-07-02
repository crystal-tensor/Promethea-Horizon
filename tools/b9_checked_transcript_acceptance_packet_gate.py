#!/usr/bin/env python3
"""T-B9-004l/T-B10-016d: checked transcript acceptance packet gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any


METHOD = "b9_checked_transcript_acceptance_packet_gate_v0"
STATUS = "checked_transcript_acceptance_packet_open_missing_artifact"
MODEL_STATUS = "checked_transcript_acceptance_packet_required_before_formal_credit"
VERSION = "0.1"
EXPECTED_PACKET_ID = "B9-checked-width-locality-transcript"
EXPECTED_PROVENANCE_MANIFEST_ID = "B9-checked-width-locality-transcript-provenance-manifest"
EXPECTED_REPLAY_MANIFEST_ID = "B9-checked-width-locality-transcript-replay-validation-manifest"
EXPECTED_ACCEPTANCE_PACKET_ID = "B9-checked-width-locality-transcript-acceptance-packet"
EXPECTED_FAILED_IDS = ["P6", "P7", "P8"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any], pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2 if pretty else None, sort_keys=True)
    path.write_text(text + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


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
    replay = load_json(args.replay_validation_manifest_gate)
    priority = load_json(args.priority_packet_gate)
    replay_summary = replay["summary"]
    priority_summary = priority["summary"]
    submission_path = args.submission_dir / f"{EXPECTED_ACCEPTANCE_PACKET_ID}.json"
    submitted_exists = submission_path.exists()
    submitted = load_json(submission_path) if submitted_exists else None

    lean_toolchain = Path("lean-toolchain")
    lakefile = Path("lakefile.lean")
    lean_module = Path("B9/ClusterStabilizer/WidthLocality.lean")
    checked_transcript = Path("results/B9_checked_run_width_locality_transcript_v0.txt")

    required_keys = [
        "acceptance_packet_id",
        "packet_id",
        "provenance_manifest_id",
        "replay_validation_manifest_id",
        "priority_packet_hash",
        "provenance_manifest_hash",
        "replay_validation_manifest_hash",
        "lean_toolchain_sha256",
        "lakefile_sha256",
        "lean_module_sha256",
        "lean_version_stdout_sha256",
        "lake_version_stdout_sha256",
        "lake_env_lean_command",
        "checked_transcript_sha256",
        "checked_transcript_stdout_sha256",
        "checked_transcript_stderr_sha256",
        "returncode",
        "elapsed_seconds",
        "checked_transcript_accepted",
        "offline_bundle_hash_manifest",
        "theorem_scope_statement",
        "open_obligation_ledger_hash",
        "claim_boundary",
        "source_evidence_files_present",
    ]
    production_required_keys = [
        "replay_validation_manifest_hash",
        "lean_toolchain_sha256",
        "lakefile_sha256",
        "lean_module_sha256",
        "lean_version_stdout_sha256",
        "lake_version_stdout_sha256",
        "lake_env_lean_command",
        "checked_transcript_sha256",
        "checked_transcript_stdout_sha256",
        "checked_transcript_stderr_sha256",
        "returncode",
        "elapsed_seconds",
        "checked_transcript_accepted",
        "offline_bundle_hash_manifest",
        "theorem_scope_statement",
        "open_obligation_ledger_hash",
        "claim_boundary",
    ]
    required_evidence_files = [
        "accepted_replay_validation_manifest",
        "lean_toolchain_file",
        "lakefile",
        "lean_module_source",
        "lean_version_stdout",
        "lake_version_stdout",
        "lake_env_lean_command_transcript",
        "checked_transcript_file",
        "checked_transcript_stdout",
        "checked_transcript_stderr",
        "returncode_and_elapsed_time_ledger",
        "offline_bundle_hash_manifest",
        "theorem_scope_statement",
        "open_obligation_ledger",
        "reproduction_environment_note",
        "claim_boundary_note",
    ]

    missing_keys = [key for key in required_keys if submitted is None or key not in submitted]
    production_present = [
        key for key in production_required_keys if submitted is not None and submitted.get(key) is not None
    ]
    manifest_bound = (
        submitted is not None
        and submitted.get("acceptance_packet_id") == EXPECTED_ACCEPTANCE_PACKET_ID
        and submitted.get("packet_id") == EXPECTED_PACKET_ID
        and submitted.get("provenance_manifest_id") == EXPECTED_PROVENANCE_MANIFEST_ID
        and submitted.get("replay_validation_manifest_id") == EXPECTED_REPLAY_MANIFEST_ID
        and submitted.get("priority_packet_hash") == replay_summary.get("priority_packet_hash")
        and submitted.get("provenance_manifest_hash") == replay_summary.get("provenance_manifest_hash")
        and submitted.get("replay_validation_manifest_hash") == replay_summary.get("manifest_hash")
    )
    source_hash_bound = (
        submitted is not None
        and submitted.get("lean_toolchain_sha256") == sha256_file(lean_toolchain)
        and submitted.get("lakefile_sha256") == sha256_file(lakefile)
        and submitted.get("lean_module_sha256") == sha256_file(lean_module)
    )
    checked_run_valid = (
        submitted is not None
        and submitted.get("returncode") == 0
        and submitted.get("checked_transcript_accepted") is True
        and bool(submitted.get("checked_transcript_sha256"))
        and checked_transcript.exists()
    )
    claim_boundary_bound = (
        submitted is not None
        and isinstance(submitted.get("claim_boundary"), dict)
        and submitted["claim_boundary"].get("formal_theorem_proved") is False
        and submitted["claim_boundary"].get("explicit_not_quantum_pcp_proof") is True
        and submitted["claim_boundary"].get("nlts_theorem_claimed") is False
        and submitted["claim_boundary"].get("global_gap_amplification_impossibility_claimed") is False
    )
    source_backed = submitted is not None and submitted.get("source_evidence_files_present") is True

    acceptance_packet = {
        "acceptance_packet_id": EXPECTED_ACCEPTANCE_PACKET_ID,
        "packet_id": EXPECTED_PACKET_ID,
        "provenance_manifest_id": EXPECTED_PROVENANCE_MANIFEST_ID,
        "replay_validation_manifest_id": EXPECTED_REPLAY_MANIFEST_ID,
        "source_replay_validation_manifest_gate": str(args.replay_validation_manifest_gate),
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "submission_artifact_path": str(submission_path),
        "priority_packet_hash": replay_summary.get("priority_packet_hash"),
        "provenance_manifest_hash": replay_summary.get("provenance_manifest_hash"),
        "replay_validation_manifest_hash": replay_summary.get("manifest_hash"),
        "blocks_acquisition_requirements": replay_summary.get("blocks_acquisition_requirements"),
        "source_hashes_at_gate_time": {
            "lean_toolchain_sha256": sha256_file(lean_toolchain),
            "lakefile_sha256": sha256_file(lakefile),
            "lean_module_sha256": sha256_file(lean_module),
        },
        "required_keys": required_keys,
        "production_required_keys": production_required_keys,
        "required_evidence_files": required_evidence_files,
        "accepted_only_if": [
            "acceptance_packet_id equals B9-checked-width-locality-transcript-acceptance-packet",
            "packet, provenance, and replay-validation identifiers match source gates",
            "priority, provenance, and replay-validation hashes match source gates",
            "Lean toolchain, lakefile, and Lean module hashes match gate-time source hashes",
            "Lean version, Lake version, lake env lean command, stdout, stderr, returncode, elapsed time, and checked transcript hash are bound",
            "returncode is 0 and checked_transcript_accepted is true before any checked transcript can count",
            "theorem_scope_statement and open_obligation_ledger keep this to a scoped checked transcript, not a Quantum PCP/NLTS theorem",
            "claim_boundary forbids Quantum PCP proof, NLTS theorem, formal theorem, and global impossibility claims",
        ],
    }
    acceptance_packet["packet_hash"] = stable_hash(acceptance_packet)

    requirements = [
        requirement(
            "P1",
            "Replay-validation manifest gate remains valid and blocked only on P6/P7/P8",
            replay.get("method") == "b9_checked_transcript_replay_validation_manifest_gate_v0"
            and replay_summary.get("validation_error_count") == 0
            and replay_summary.get("failed_manifest_requirement_ids") == EXPECTED_FAILED_IDS,
            {
                "source_status": replay.get("status"),
                "failed_manifest_requirement_ids": replay_summary.get("failed_manifest_requirement_ids"),
                "validation_error_count": replay_summary.get("validation_error_count"),
            },
        ),
        requirement(
            "P2",
            "Priority checked transcript packet remains fixed and source-shaped",
            priority.get("method") == "b9_checked_transcript_priority_packet_gate_v0"
            and priority_summary.get("priority_packet_id") == EXPECTED_PACKET_ID
            and priority_summary.get("validation_error_count") == 0
            and priority_summary.get("failed_priority_requirement_ids") == EXPECTED_FAILED_IDS,
            {
                "priority_packet_id": priority_summary.get("priority_packet_id"),
                "packet_hash": priority_summary.get("packet_hash"),
                "failed_priority_requirement_ids": priority_summary.get("failed_priority_requirement_ids"),
            },
        ),
        requirement(
            "P3",
            "Acceptance packet carries locked checked transcript schema and evidence classes",
            len(required_keys) == 24
            and len(production_required_keys) == 17
            and len(required_evidence_files) == 16,
            {
                "required_key_count": len(required_keys),
                "production_required_key_count": len(production_required_keys),
                "required_evidence_file_count": len(required_evidence_files),
            },
        ),
        requirement(
            "P4",
            "Pinned Lean project source hashes remain stable at the acceptance gate",
            lean_toolchain.exists()
            and lakefile.exists()
            and lean_module.exists()
            and sha256_file(lean_toolchain) == replay_summary.get("lean_toolchain_sha256")
            and sha256_file(lakefile) == replay_summary.get("lakefile_sha256")
            and sha256_file(lean_module) == replay_summary.get("lean_module_sha256"),
            {
                "lean_toolchain_sha256": sha256_file(lean_toolchain),
                "lakefile_sha256": sha256_file(lakefile),
                "lean_module_sha256": sha256_file(lean_module),
            },
        ),
        requirement(
            "P5",
            "Current state has no accepted checked transcript or theorem claim",
            replay_summary.get("checked_transcript_present") is False
            and replay_summary.get("proof_assistant_checked") is False
            and replay_summary.get("formal_theorem_proved") is False
            and replay_summary.get("explicit_not_quantum_pcp_proof") is True
            and replay_summary.get("nlts_theorem_claimed") is False
            and replay_summary.get("global_gap_amplification_impossibility_claimed") is False,
            {
                "checked_transcript_present": replay_summary.get("checked_transcript_present"),
                "proof_assistant_checked": replay_summary.get("proof_assistant_checked"),
                "formal_theorem_proved": replay_summary.get("formal_theorem_proved"),
                "explicit_not_quantum_pcp_proof": replay_summary.get("explicit_not_quantum_pcp_proof"),
                "nlts_theorem_claimed": replay_summary.get("nlts_theorem_claimed"),
                "global_gap_amplification_impossibility_claimed": replay_summary.get(
                    "global_gap_amplification_impossibility_claimed"
                ),
            },
        ),
        requirement(
            "P6",
            "Checked transcript acceptance packet has been submitted",
            submitted_exists,
            {"submission_artifact_path": str(submission_path), "exists": submitted_exists},
        ),
        requirement(
            "P7",
            "Submitted acceptance packet satisfies the locked checked transcript schema",
            submitted_exists and not missing_keys and len(production_present) == len(production_required_keys),
            {
                "missing_keys": missing_keys,
                "production_keys_present": production_present,
                "production_required_keys": production_required_keys,
                "submitted_key_count": len(submitted) if submitted else 0,
            },
        ),
        requirement(
            "P8",
            "Submitted acceptance packet is source-backed, manifest-bound, source-hash-bound, checked-run-valid, and claim-boundary-bound",
            source_backed
            and manifest_bound
            and source_hash_bound
            and checked_run_valid
            and claim_boundary_bound,
            {
                "source_backed": source_backed,
                "manifest_bound": manifest_bound,
                "source_hash_bound": source_hash_bound,
                "checked_run_valid": checked_run_valid,
                "claim_boundary_bound": claim_boundary_bound,
            },
        ),
        requirement(
            "P9",
            "Forbidden Quantum PCP, NLTS, formal theorem, and global impossibility claims remain false",
            replay_summary.get("formal_theorem_proved") is False
            and replay_summary.get("explicit_not_quantum_pcp_proof") is True
            and replay_summary.get("nlts_theorem_claimed") is False
            and replay_summary.get("global_gap_amplification_impossibility_claimed") is False,
            {
                "formal_theorem_proved": replay_summary.get("formal_theorem_proved"),
                "explicit_not_quantum_pcp_proof": replay_summary.get("explicit_not_quantum_pcp_proof"),
                "nlts_theorem_claimed": replay_summary.get("nlts_theorem_claimed"),
                "global_gap_amplification_impossibility_claimed": replay_summary.get(
                    "global_gap_amplification_impossibility_claimed"
                ),
            },
        ),
    ]

    passed = sum(row["passed"] for row in requirements)
    failed_ids = [row["requirement_id"] for row in requirements if not row["passed"]]
    validation_errors: list[str] = []
    if failed_ids != EXPECTED_FAILED_IDS:
        validation_errors.append(f"unexpected checked transcript acceptance failures: {failed_ids}")
    if submitted_exists:
        validation_errors.append("gate expected no submitted acceptance packet until a proof-agent PR supplies one")

    summary = {
        "acceptance_packet_id": EXPECTED_ACCEPTANCE_PACKET_ID,
        "packet_id": EXPECTED_PACKET_ID,
        "provenance_manifest_id": EXPECTED_PROVENANCE_MANIFEST_ID,
        "replay_validation_manifest_id": EXPECTED_REPLAY_MANIFEST_ID,
        "priority_packet_hash": replay_summary.get("priority_packet_hash"),
        "provenance_manifest_hash": replay_summary.get("provenance_manifest_hash"),
        "replay_validation_manifest_hash": replay_summary.get("manifest_hash"),
        "acceptance_packet_hash": acceptance_packet["packet_hash"],
        "acceptance_requirement_count": len(requirements),
        "acceptance_requirements_passed": passed,
        "acceptance_requirements_failed": len(requirements) - passed,
        "failed_acceptance_requirement_ids": failed_ids,
        "required_key_count": len(required_keys),
        "production_required_key_count": len(production_required_keys),
        "required_evidence_file_count": len(required_evidence_files),
        "blocks_acquisition_requirements": replay_summary.get("blocks_acquisition_requirements"),
        "lean_toolchain_sha256": sha256_file(lean_toolchain),
        "lakefile_sha256": sha256_file(lakefile),
        "lean_module_sha256": sha256_file(lean_module),
        "submitted_acceptance_packet_exists": submitted_exists,
        "submitted_key_count": len(submitted) if submitted else 0,
        "missing_key_count": len(missing_keys),
        "production_keys_present_count": len(production_present),
        "checked_transcript_present": False,
        "checked_transcript_accepted": False,
        "proof_assistant_checked": False,
        "formal_theorem_proved": False,
        "explicit_not_quantum_pcp_proof": True,
        "nlts_theorem_claimed": False,
        "global_gap_amplification_impossibility_claimed": False,
        "validation_error_count": len(validation_errors),
    }
    return {
        "benchmark_id": "B9",
        "linked_benchmark_id": "B10",
        "source_target_id": "B10-T3",
        "title": "B9 Checked Transcript Acceptance Packet Gate",
        "version": VERSION,
        "last_updated": args.last_updated,
        "method": METHOD,
        "status": STATUS,
        "model_status": MODEL_STATUS,
        "source_replay_validation_manifest_gate": str(args.replay_validation_manifest_gate),
        "source_priority_packet_gate": str(args.priority_packet_gate),
        "summary": summary,
        "checked_transcript_acceptance_packet": acceptance_packet,
        "requirements": requirements,
        "claim_boundary": {
            "what_is_supported": (
                "The B9/B10 proof-assistant route now has an acceptance packet defining what a "
                "source-backed Lean/Lake checked transcript must contain before it can count."
            ),
            "what_is_not_supported": (
                "No checked transcript acceptance packet or checked transcript has been submitted or accepted; "
                "no formal theorem, Quantum PCP proof, NLTS theorem, or global impossibility claim is supported."
            ),
            "next_gate": (
                "Submit B9-checked-width-locality-transcript-acceptance-packet with replay manifest hash, "
                "Lean/Lake version transcripts, lake env lean transcript, stdout/stderr hashes, returncode 0, "
                "offline bundle hash, theorem scope, open-obligation ledger, and claim boundary."
            ),
            "proof_assistant_checked": False,
            "formal_theorem_proved": False,
            "explicit_not_quantum_pcp_proof": True,
            "nlts_theorem_claimed": False,
            "global_gap_amplification_impossibility_claimed": False,
        },
        "validation_errors": validation_errors,
        "runtime_seconds": round(time.time() - started, 6),
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    summary = payload["summary"]
    packet = payload["checked_transcript_acceptance_packet"]
    lines = [
        "# B9 Checked Transcript Acceptance Packet Gate",
        "",
        f"Status: `{payload['status']}`",
        "",
        "## Summary",
        "",
        f"- Method: `{payload['method']}`",
        f"- Acceptance packet: `{summary['acceptance_packet_id']}`",
        f"- Checked transcript packet: `{summary['packet_id']}`",
        f"- Replay-validation manifest: `{summary['replay_validation_manifest_id']}`",
        f"- Replay-validation manifest hash: `{summary['replay_validation_manifest_hash']}`",
        f"- Priority packet hash: `{summary['priority_packet_hash']}`",
        f"- Acceptance packet hash: `{summary['acceptance_packet_hash']}`",
        f"- Requirements passed/failed: `{summary['acceptance_requirements_passed']}` / `{summary['acceptance_requirements_failed']}`",
        f"- Failed requirement IDs: `{summary['failed_acceptance_requirement_ids']}`",
        f"- Required key / production key / evidence file count: `{summary['required_key_count']}` / `{summary['production_required_key_count']}` / `{summary['required_evidence_file_count']}`",
        f"- Blocks acquisition requirements: `{summary['blocks_acquisition_requirements']}`",
        f"- Checked transcript present / accepted: `{summary['checked_transcript_present']}` / `{summary['checked_transcript_accepted']}`",
        f"- proof_assistant_checked: `{summary['proof_assistant_checked']}`",
        f"- formal_theorem_proved: `{summary['formal_theorem_proved']}`",
        f"- explicit_not_quantum_pcp_proof: `{summary['explicit_not_quantum_pcp_proof']}`",
        f"- validation_error_count: `{summary['validation_error_count']}`",
        "",
        "## Acceptance Packet",
        "",
        f"- Submission path: `{packet['submission_artifact_path']}`",
        f"- Packet hash: `{packet['packet_hash']}`",
        "",
        "Required evidence files:",
        "",
    ]
    for item in packet["required_evidence_files"]:
        lines.append(f"- {item}")
    lines.extend(["", "Acceptance predicates:", ""])
    for item in packet["accepted_only_if"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Requirement Results", ""])
    for row in payload["requirements"]:
        state = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {row['requirement_id']} [{state}]: {row['label']}")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Supported: {payload['claim_boundary']['what_is_supported']}",
            f"- Not supported: {payload['claim_boundary']['what_is_not_supported']}",
            f"- Next gate: {payload['claim_boundary']['next_gate']}",
            f"- proof_assistant_checked: {payload['claim_boundary']['proof_assistant_checked']}",
            f"- formal_theorem_proved: {payload['claim_boundary']['formal_theorem_proved']}",
            f"- explicit_not_quantum_pcp_proof: {payload['claim_boundary']['explicit_not_quantum_pcp_proof']}",
            f"- nlts_theorem_claimed: {payload['claim_boundary']['nlts_theorem_claimed']}",
            f"- global_gap_amplification_impossibility_claimed: {payload['claim_boundary']['global_gap_amplification_impossibility_claimed']}",
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
        "--replay-validation-manifest-gate",
        type=Path,
        default=Path("results/B9_checked_transcript_replay_validation_manifest_gate_v0.json"),
    )
    parser.add_argument(
        "--priority-packet-gate",
        type=Path,
        default=Path("results/B9_checked_transcript_priority_packet_gate_v0.json"),
    )
    parser.add_argument("--submission-dir", type=Path, default=Path("research/submissions"))
    parser.add_argument(
        "--json-output",
        type=Path,
        default=Path("results/B9_checked_transcript_acceptance_packet_gate_v0.json"),
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=Path("research/B9_checked_transcript_acceptance_packet_gate.md"),
    )
    parser.add_argument("--last-updated", default="2026-07-03")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    payload = build_payload(args)
    write_json(args.json_output, payload, args.pretty)
    write_markdown(payload, args.markdown_output)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["validation_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
